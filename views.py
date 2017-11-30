# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from mothulity.forms import FileFieldForm, OptionsForm
from mothulity.models import JobID, SubmissionData
import utils
import uuid
import os

# Create your views here.


def index(request):
    if request.method == "POST":
        form = FileFieldForm(request.POST,
                             request.FILES)
        if form.is_valid():
            job_id = uuid.uuid4()
            upld_dir = "{}{}/".format(settings.MEDIA_URL,
                                      job_id)
            os.system("mkdir {}".format(upld_dir))
            upld_files = request.FILES.getlist("file_field")
            for upfile in upld_files:
                utils.write_file(upfile,
                                 upld_dir)
                utils.chmod_file("{}{}".format(upld_dir,
                                               upfile),
                                 mod=666)
                if utils.sniff_file("{}{}".format(upld_dir,
                                                  upfile),
                                    "fastq") is True:
                    pass
                else:
                    os.system("rm -r {}".format(upld_dir))
                    form = FileFieldForm()
                    return render(request,
                                  "mothulity/index.html.jj2",
                                  {"form": form,
                                   "upload_error": True})
            job = JobID(job_id=job_id)
            job.save()
            form = OptionsForm()
            return render(request,
                          "mothulity/options.html.jj2",
                          {"form": form,
                           "job": job_id})
    else:
        form = FileFieldForm()
    return render(request,
                  "mothulity/index.html.jj2",
                  {"form": form})


def submit(request,
           job):
    job = get_object_or_404(JobID, job_id=job)
    sub_data = job.submissiondata_set.create(job_name=request.POST["job_name"],
                                             notify_email=request.POST["notify_email"],
                                             max_ambig=request.POST["max_ambig"],
                                             max_homop=request.POST["max_homop"],
                                             min_length=request.POST["min_length"],
                                             max_length=request.POST["max_length"],
                                             min_overlap=request.POST["min_overlap"],
                                             screen_criteria=request.POST["screen_criteria"],
                                             chop_length=request.POST["chop_length"],
                                             precluster_diffs=request.POST["precluster_diffs"],
                                             classify_seqs_cutoff=request.POST["classify_seqs_cutoff"],
                                             amplicon_type=request.POST["amplicon_type"])
    moth_cmd_dict = {"job-name": sub_data.job_name,
                     "notify-email": sub_data.notify_email,
                     "max-ambig": sub_data.max_ambig,
                     "max-homop": sub_data.max_homop,
                     "min-length": sub_data.min_length,
                     "max-length": sub_data.max_length,
                     "min-overlap": sub_data.min_overlap,
                     "screen-criteria": sub_data.screen_criteria,
                     "chop-length": sub_data.chop_length,
                     "precluster-diffs": sub_data.chop_length,
                     "classify-seqs-cutoff": sub_data.classify_seqs_cutoff,
                     "amplicon-type": sub_data.amplicon_type}
    moth_cmd = utils.render_moth_cmd(moth_options=moth_cmd_dict)
    job_id_link = "".format(job.job_id)
    return render(request,
                  "mothulity/submit.html.jj2",
                  {"notify_email": request.POST["notify_email"],
                   "job_id": job.job_id,
                   "moth_cmd": moth_cmd})
