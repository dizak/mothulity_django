# -*- coding: utf-8 -*-

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from mothulity.forms import FileFieldForm, OptionsForm, ResendResultsEMailForm
from mothulity.models import *
from mothulity.utils import isdone
from . import utils
import uuid
import subprocess as sp

upload_errors = {
    'uneven': 'Sorry, it seems you uploaded an uneven number of files...',
    'mothulity_fc': 'Sorry, it seems there is something wrong with your file names...',
    'format': 'Sorry, it seems you uploaded something else than FASTQ file...'
}

def index(request):
    """
    Evaluates file upload form, uploaded files, total number of reads, creates
    Job ID and renders appropriate template.

    Parameters
    -------
    request: HTTP.request

    Return
    ------
    django.template
        Template rendered to HTML.
    """
    site = Site.objects.get(domain=[i for i in settings.ALLOWED_HOSTS if i != 'localhost'][0])
    path_settings = site.pathsettings
    web_server_settings = site.webserversettings
    hpc_settings = site.hpcsettings
    request.session.set_expiry(web_server_settings.files_upload_expiry_time)
    if request.method == "POST":
        form = FileFieldForm(request.POST,
                             request.FILES)
        if form.is_valid():
            job_id = uuid.uuid4()
            upld_dir = "{}{}/".format(path_settings.upload_path,
                                      str(job_id).replace("-", "_"))
            hpc_dir = "{}{}/".format(
                path_settings.hpc_path,
                str(job_id).replace("-", "_"),
            )
            sp.check_output("mkdir {}".format(upld_dir), shell=True).decode('utf-8')
            upld_files = request.FILES.getlist("file_field")
            if len(upld_files) % 2 != 0:
                sp.check_output("rm -r {}".format(upld_dir), shell=True).decode('utf-8')
                form = FileFieldForm()
                return render(request,
                              "mothulity/index.html.jj2",
                              {"articles": Article.objects.all(),
                               "form": form,
                               "upload_error": upload_errors['uneven']})
            for upfile in upld_files:
                utils.write_file(upfile,
                                 upld_dir)
                utils.chmod_file("{}{}".format(upld_dir,
                                               upfile),
                                 mod=666)
                if utils.sniff_file("{}{}".format(upld_dir,
                                                  upfile),
                                    "fastq") is not True:
                    sp.check_output("rm -r {}".format(upld_dir), shell=True).decode('utf-8')
                    form = FileFieldForm()
                    return render(request,
                                  "mothulity/index.html.jj2",
                                  {"articles": Article.objects.all(),
                                   "form": form,
                                   "upload_error": upload_errors['format']})
            try:
                utils.ssh_cmd(cmd='mothulity_fc {}'.format(hpc_dir), machine=hpc_settings.hpc_name)
            except:
                form = FileFieldForm()
                return render(request,
                              "mothulity/index.html.jj2",
                              {"articles": Article.objects.all(),
                               "form": form,
                               "upload_error": upload_errors['mothulity_fc']})
            seqs_count = utils.count_seqs("{}*fastq".format(upld_dir))
            job = JobID(job_id=job_id)
            job.save()
            seqsstats = SeqsStats(job_id=job, seqs_count=seqs_count)
            seqsstats.save()
            form = OptionsForm()
            return render(request,
                          "mothulity/options.html.jj2",
                          {"articles": Article.objects.all(),
                           "form": form,
                           "job": job_id})
    else:
        form = FileFieldForm()
    return render(request,
                  "mothulity/index.html.jj2",
                  {"articles": Article.objects.all(),
                   "form": form})


def submit(request,
           job):
    """
    Evaluates options form retrieves Job ID and its properties, renders
    appropriate template.

    Parameters
    -------
    request: HTTP.request
    job: str
        Job ID

    Return
    ------
    django.template
        Template rendered to HTML.
    """
    if request.method == "POST":
        form = OptionsForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            job = get_object_or_404(JobID, job_id=job)
            submissiondata = SubmissionData(job_id=job, **form_data)
            submissiondata.save()
            jobstatus = JobStatus(job_id=job, job_status="pending")
            jobstatus.save()
            return render(request,
                          "mothulity/submit.html.jj2",
                          {"articles": Article.objects.all(),
                           "submissiondata": job.submissiondata,
                           "notify_email": request.POST["notify_email"],
                           "job_id": job.job_id})
        else:
            return render(request,
                          "mothulity/options.html.jj2",
                          {"articles": Article.objects.all(),
                           "form": form,
                           "job": job})


def status(request,
           job):
    job = get_object_or_404(JobID, job_id=job)
    site = Site.objects.get(
        domain=[i for i in settings.ALLOWED_HOSTS if i != 'localhost'][0]
        )
    path_settings = site.pathsettings
    web_server_settings = site.webserversettings
    hpc_settings = site.hpcsettings
    hpc_dir = "{}{}/".format(
        path_settings.hpc_path,
        str(job.job_id).replace("-", "_"),
    )
    if request.method == 'POST':
        form = ResendResultsEMailForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            print(form_data)
            utils.ssh_cmd(
                cmd='''"cd {0} && headnode_notifier.py {1} --subject {2} --attach analysis_{2}.zip"'''.format(
                    hpc_dir,
                    form_data['email_address'],
                    job.submissiondata.job_name,
                ),
                machine=hpc_settings.hpc_name,
            )
    else:
        form = ResendResultsEMailForm()
    return render(request,
                  "mothulity/status.html.jj2",
                  {
                      "articles": Article.objects.all(),
                       "submissiondata": job.submissiondata,
                       "jobstatus": job.jobstatus,
                       "max_retry": hpc_settings.retry_maximum_number + 1,
                       'form': form,
                   })


def wiki(request,
         title):
    """
    Displays small wiki articles created with models.Article.
    """
    title = request.path.split("/")[-1]
    return render(request,
                  "mothulity/wiki.html.jj2",
                  {"title": title,
                   "articles": Article.objects.all()})

def handler404(request):
    """
    Displays custom 404 error page.
    """
    return render(
        request,
        'mothulity/404.html.jj2',
        status=404,
        )

def handler413(request):
    """
    Displays custom 413 error page.
    """
    return render(
        request,
        'mothulity/413.html.jj2',
        status=413,
        )

def handler500(request):
    """
    Displays custom 500 error page.
    """
    return render(
        request,
        'mothulity/500.html.jj2',
        status=500,
        )
