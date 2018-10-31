# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.sites.models import Site
from froala_editor.fields import FroalaField
from django.utils import timezone
import pytz

# Create your models here.


class JobID(models.Model):
    job_id = models.CharField(max_length=50)

    def __str__(self):
        return self.job_id


class SeqsStats(models.Model):
    job_id = models.OneToOneField(JobID,
                                  on_delete=models.CASCADE,
                                  primary_key=True)
    seqs_count = models.IntegerField()

    def __int__(self):
        return self.seqs_count


class SubmissionData(models.Model):
    job_id = models.OneToOneField(JobID,
                                  on_delete=models.CASCADE,
                                  primary_key=True)
    job_name = models.CharField(max_length=20)
    notify_email = models.CharField(max_length=40)
    max_ambig = models.IntegerField()
    max_homop = models.IntegerField()
    # min_length = models.IntegerField()
    # max_length = models.IntegerField()
    min_overlap = models.IntegerField()
    screen_criteria = models.IntegerField()
    chop_length = models.IntegerField()
    precluster_diffs = models.IntegerField()
    classify_seqs_cutoff = models.IntegerField()
    amplicon_type = models.CharField(max_length=3)

    def __str__(self):
        return self.job_name


class JobStatus(models.Model):
    """
    Model for job status description.

    Parameters
    -------
    added_time: int
        Number of times a job has been submitted.
    """
    job_id = models.OneToOneField(JobID,
                                  on_delete=models.CASCADE,
                                  primary_key=True)
    job_status = models.CharField(max_length=10)
    slurm_id = models.IntegerField(null=True)
    retry = models.IntegerField(default=0)
    submission_time = models.DateTimeField("submission time",
                                           default=timezone.now)

    def __str__(self):
        return self.job_status


class Article(models.Model):
    """
    Model for small wiki articles.
    """
    title = models.CharField(max_length=100)
    content = FroalaField()


class PathSettings(models.Model):
    """
    Model for the upload and HPC paths.
    """
    site = models.OneToOneField(Site, on_delete=models.CASCADE)
    upload_path = models.CharField(
        default='/mnt/mothulity_HPC/jobs/',
        max_length=300,
        help_text='Input files upload path. It must point to the location ON THE WEBSERVER which also MOUNTED FROM HPC. MUST CONTAIN TRAILING SLASH.',
        )
    hpc_prefix_path = models.CharField(
        default='/home/mothulity/jobs/',
        max_length=300,
        help_text='Must point to the same location as the above upload_path but from the HPC ITSELF. MUST CONTAIN TRAILING SLASH.'
    )


class HPCSettings(models.Model):
    """
    Model for HPC setting, eg. the minimum number of free nodes.
    """
    site = models.OneToOneField(Site, on_delete=models.CASCADE)
    free_Ns_minimum_number = models.IntegerField(
        default=20,
        help_text='Minimum number of free N nodes in order to submit the job.',
        )
    free_PHIs_minimum_number = models.IntegerField(
        default=5,
        help_text='Minimum number of free PHI nodes in order to submit the job.',
        )
    retry_maximum_number = models.IntegerField(
        default=1,
        help_text='Maximum number of resubmissions before a failed job is removed.'
        )
    scheduler_interval = models.IntegerField(
        default=300,
        help_text='Time interval (in seconds) for the scheduler. Values above 30 are recommended due to the delays in the database and SLURM communication. For changes to apply the scheduler services must be restarted.'
        )
