#! /usr/bin/env python


import os
import sys
import schedule

import django
from django.conf import settings

sys.path.append(os.path.abspath(sys.argv[1]))
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "{}.settings".format(
        [i for i in os.path.abspath(sys.argv[1]).split('/') if len(i) > 0][-1]
        ),
    )
django.setup()

from mothulity import utils
from mothulity import models

site = models.Site.objects.get(
    domain=[i for i in settings.ALLOWED_HOSTS if i != 'localhost'][0]
    )
hpc_settings = site.hpcsettings


def job():
    """
    Retrieve pending jobs and submit them properly to the computing cluster.
    """
    site = models.Site.objects.get(
        domain=[i for i in settings.ALLOWED_HOSTS if i != 'localhost'][0]
        )
    hpc_settings = site.hpcsettings
    path_settings = site.pathsettings
    web_server_settings = site.webserversettings
    for i in utils.get_pending_ids():
        print("\nJobID {} Status: pending\n".format(i))
        idle_ns = utils.parse_sinfo(utils.ssh_cmd(cmd="sinfo", machine=hpc_settings.hpc_name), "long", "idle")
        idle_phis = utils.parse_sinfo(utils.ssh_cmd(cmd="sinfo", machine=hpc_settings.hpc_name), "accel", "idle")
        print("Number of free ns - {}. Number of free phis  - {}".format(
            idle_ns,
            idle_phis,
        ))
        if idle_phis > hpc_settings.free_PHIs_minimum_number:
            if utils.queue_submit(job_id=i, machine=hpc_settings.hpc_name, hpc_path=path_settings.hpc_path) is True:
                utils.change_status(i)
                print("JobID {} submitted".format(i))
        else:
            print("Only {} phi nodes free. {} phi must stay free".format(idle_phis,
                                                                         hpc_settings.free_PHIs_minimum_number))
        if idle_ns > hpc_settings.free_Ns_minimum_number:
            if utils.queue_submit(job_id=i, machine=hpc_settings.hpc_name, hpc_path=path_settings.hpc_path) is True:
                utils.change_status(i)
                print("JobID {} submitted".format(i))
        else:
            print("Only {} n nodes free. {} n nodes must stay free".format(idle_ns,
                                                                           hpc_settings.free_Ns_minimum_number))
    for i in utils.get_ids_with_status("submitted"):
        print("\nJobID {} Status: submitted. Retries: {}\n".format(i,
                                                                   utils.get_retry(i)))
        job_sshfs_dir = "{}{}/".format(path_settings.upload_path, str(i).replace("-", "_"))
        if utils.isrunning(job_id=i, machine=hpc_settings.hpc_name) is False and utils.isdone(job_sshfs_dir, '*shared') is False and utils.get_retry(i) >= hpc_settings.retry_maximum_number:
            print("JobID above retry limit. Changing its status to <dead>")
            utils.change_status(i, "dead")
            break
        if utils.isrunning(job_id=i, machine=hpc_settings.hpc_name) is False and utils.isdone(job_sshfs_dir, '*shared') is False and utils.get_retry(i) < hpc_settings.retry_maximum_number:
            print("JobID {} is NOT done and is NOT runnning. Will be resubmitted".format(i))
            utils.remove_except(job_sshfs_dir, 'fastq', safety=False)
            utils.change_status(i, "pending")
            utils.add_retry(i, utils.get_retry(i) + 1)
            break
        if utils.isrunning(job_id=i, machine=hpc_settings.hpc_name) is False and utils.isdone(job_sshfs_dir, filename="*shared") is True:
            print("JobID {} is done".format(i))
            utils.change_status(i, "done")
            break
    for i in utils.get_ids_with_status("done"):
        print("\nJobID {} Status: done.\n".format(i))
        job_sshfs_dir = "{}{}/".format(path_settings.upload_path, str(i).replace("-", "_"))
        if utils.isdone(job_sshfs_dir, filename='*zip'):
            utils.remove_except(job_sshfs_dir, '*zip', safety=False)
            utils.change_status(i, 'closed')
    for i in utils.get_dirs_without_entries(path_settings.upload_path):
        if utils.isstale(i, web_server_settings.files_upload_expiry_time):
            print("{} is old and has no JobID. Removing it".format(i))
            utils.remove_dir(i, safety=False)


schedule.every(hpc_settings.scheduler_interval).seconds.do(job)


def main():
    while True:
        schedule.run_pending()


if __name__ == '__main__':
    main()
