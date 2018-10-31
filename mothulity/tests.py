# -*- coding: utf-8 -*-

from django.test import TestCase
import unittest
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
import socket
import pytz
from io import BytesIO
import os
import uuid
from random import randint
from mothulity import views, models, forms, utils

base_dir = os.path.abspath(os.path.dirname(__file__))
hostname_production = 'xe-mothulity-dizak'
hostname_development = 'bender'

class UtilsTests(TestCase):
    """
    Tests for uploaded files validator.
    """
    def setUp(self):
        """
        Sets up class level attributes for the tests.

        Parameters
        -------
        fastq_file: str
            Path to test fastq file.
        summ_file: str
            Path to test non-fastq file.
        sinfo_raw: str
            Path to test sinfo log file.
        long_idle_nodes: int, <61>
            Number of nodes idle in queue long.
        """
        self.test_job_id = str(uuid.uuid4())
        self.fastq_file = "{}/tests/Mock_S280_L001_R1_001.fastq".format(base_dir)
        self.summ_file = "{}/tests/mothur.job.trim.contigs.summary".format(base_dir)
        self.machine = "headnode"
        self.cmd = "uname"
        self.cmd_out = "Linux"
        self.sinfo_file = "{}/tests/sinfo.log".format(base_dir)
        self.squeue_file = "{}/tests/squeue.log".format(base_dir)
        self.long_idle_nodes = 61
        self.accel_idle_nodes = 12
        self.accel_alloc_nodes = 3
        self.JOBID_1 = 1324233
        self.JOBID_2 = 1324490
        self.PARTITION_1 = "accel"
        self.NAME_1 = "bash"
        self.USER_1 = "maciek"
        self.ST_1 = "R"
        self.TIME_1 = "13-09:03:01"
        self.NODES_1 = 1
        self.NODELIST_1 = "phi3"
        self.PARTITION_2 = "short"
        self.NAME_2 = "bash"
        self.USER_2 = "huncwot"
        self.ST_2 = "R"
        self.TIME_2 = "5:00:01"
        self.NODES_2 = 1
        self.NODELIST_2 = "n1"
        self.ref_moth_cmd = 'mothulity tests --output-dir tests --run bash --job-name test_job'
        self.test_moth_files = 'tests'
        self.test_moth_cmd_dict = {
            'job_name': 'test job',
            'id': self.test_job_id,
            'job_id_id': self.test_job_id,
            'amplicon_type': '16S',
        }
        self.test_job_dir = '{}/tests/{}/'.format(base_dir, self.test_job_id)
        os.system('mkdir {}'.format(self.test_job_dir))
        os.system('touch {0}1.fastq {0}2.fastq {0}mothur.job.sh {0}analysis_mothur.job.zip'.format(self.test_job_dir))
        self.ref_files_to_spare = ['analysis_mothur.job.zip']

    def tearDown(self):
        """
        Distroys tests left-overs.
        """
        os.system('rm -r {}'.format(self.test_job_dir))

    def test_sniff_true(self):
        """
        Tests whether utils.sniff returns <True> on fastq file.
        """
        self.assertIs(utils.sniff_file(self.fastq_file), True)

    def test_sniff_false(self):
        """
        Tests whether utils.sniff returns <False> on fastq file.
        """
        self.assertIs(utils.sniff_file(self.summ_file), False)

    def test_count_seqs(self):
        """
        Tests whether utils.count_seqs return expected reads number.
        """
        self.assertEqual(utils.count_seqs(self.fastq_file), 4779)


    def test_parse_sinfo(self):
        """
        Tests whether sinfo log file returns expected values.
        """
        with open(self.sinfo_file) as fin:
            sinfo_str = fin.read()
        self.assertEqual(utils.parse_sinfo(sinfo_str,
                                           partition="long",
                                           state="idle"),
                         self.long_idle_nodes)
        self.assertEqual(utils.parse_sinfo(sinfo_str,
                                           partition="accel",
                                           state="idle"),
                         self.accel_idle_nodes)
        self.assertEqual(utils.parse_sinfo(sinfo_str,
                                           partition="accel",
                                           state="alloc"),
                         self.accel_alloc_nodes)

    def test_parse_squeue(self):
        """
        Test whether squeue log file returns expected values
        """
        with open(self.squeue_file) as fin:
            squeue_str = fin.read()
        self.assertEqual(utils.parse_squeue(squeue_str,
                                            self.JOBID_1,
                                            "JOBID"),
                         self.JOBID_1)
        self.assertEqual(utils.parse_squeue(squeue_str,
                                            self.JOBID_1,
                                            "PARTITION"),
                         self.PARTITION_1)
        self.assertEqual(utils.parse_squeue(squeue_str,
                                            self.JOBID_1,
                                            "NAME"),
                         self.NAME_1)
        self.assertEqual(utils.parse_squeue(squeue_str,
                                            self.JOBID_1,
                                            "USER"),
                         self.USER_1)
        self.assertEqual(utils.parse_squeue(squeue_str,
                                            self.JOBID_1,
                                            "ST"),
                         self.ST_1)
        self.assertEqual(utils.parse_squeue(squeue_str,
                                            self.JOBID_1,
                                            "TIME"),
                         self.TIME_1)
        self.assertEqual(utils.parse_squeue(squeue_str,
                                            self.JOBID_2,
                                            "JOBID"),
                         self.JOBID_2)
        self.assertEqual(utils.parse_squeue(squeue_str,
                                            self.JOBID_2,
                                            "PARTITION"),
                         self.PARTITION_2)
        self.assertEqual(utils.parse_squeue(squeue_str,
                                            self.JOBID_2,
                                            "NAME"),
                         self.NAME_2)
        self.assertEqual(utils.parse_squeue(squeue_str,
                                            self.JOBID_2,
                                            "USER"),
                         self.USER_2)
        self.assertEqual(utils.parse_squeue(squeue_str,
                                            self.JOBID_2,
                                            "ST"),
                         self.ST_2)
        self.assertEqual(utils.parse_squeue(squeue_str,
                                            self.JOBID_2,
                                            "TIME"),
                         self.TIME_2)

    # def test_ssh_cmd(self):
    #     """
    #     Tests whether commands via ssh are successful.
    #     """
    #     self.assertEqual(utils.ssh_cmd(self.cmd,
    #                                    self.machine),
    #                      self.cmd_out)

    def test_render_moth_cd(self):
        """
        Tests if the mothulity command is properly rendered.
        """
        self.assertEqual(
            sorted(self.ref_moth_cmd.split(' ')),
            sorted(utils.render_moth_cmd(
                moth_files=self.test_moth_files,
                moth_opts=self.test_moth_cmd_dict,
                shell='bash'
                ).split(' '))
        )

    def test_remove_except(self):
        """
        Tests whether only unwanted files are being removed.
        """
        utils.remove_except(self.test_job_dir, '*zip', safety=False)
        self.test_job_dir_content = os.listdir(self.test_job_dir)
        self.assertEqual(
            self.test_job_dir_content,
            self.ref_files_to_spare
            )

    def test_isdone(self):
        """
        Tests if returns proper value.
        """
        self.assertTrue(utils.isdone(self.test_job_dir))
        self.assertFalse(utils.isdone(self.test_job_dir, '*foobar'))


class ViewsResponseTests(TestCase):
    """
    Tests for the response codes.
    """
    def setUp(self):
        """
        Sets up class level attributes for the tests.

        Parameters
        -------
        urls_list: list of str
            List urls postfixes to be tested by django's test client.
        """
        self.settings_domain = [
            i for i in settings.ALLOWED_HOSTS if i != 'localhost'
        ][0]
        site = models.Site(id=randint(1, 10))
        site.domain = self.settings_domain
        site.name = 'mothulity'
        site.save()
        path_settings = models.PathSettings(
            site=site,
            upload_path='/tmp/',
            hpc_prefix_path='/tmp/',
        )
        path_settings.save()
        hpc_settings = models.HPCSettings(
            site=site,
            free_Ns_minimum_number=20,
            free_PHIs_minimum_number=5,
            retry_maximum_number=1,
            scheduler_interval=300,
        )
        hpc_settings.save()
        self.test_job_id = str(uuid.uuid4())
        self.submission_data_dict = {"job_name": "test-job",
                                     "notify_email": "test@mail.com",
                                     "max_ambig": 0,
                                     "max_homop": 8,
                                     # "min_length": 100,
                                     # "max_length": 200,
                                     "min_overlap": 10,
                                     "screen_criteria": 95,
                                     "chop_length": 250,
                                     "precluster_diffs": 2,
                                     "classify_seqs_cutoff": 80,
                                     "amplicon_type": "16S"}
        self.test_seqs_count = 42
        self.test_job_status = "pending"
        self.test_submission_time = timezone.now()
        self.j_id = models.JobID(job_id=self.test_job_id)
        self.j_id.save()
        stats = models.SeqsStats(job_id=self.j_id,
                                 seqs_count=self.test_seqs_count)
        stats.save()
        status = models.JobStatus(job_id=self.j_id,
                                  job_status=self.test_job_status,
                                  submission_time=self.test_submission_time)
        status.save()
        submissiondata = models.SubmissionData(job_id=self.j_id,
                                             **self.submission_data_dict)
        submissiondata.save()
        self.ref_single_file_name = '{}/tests/Mock_S280_L001_R1_001.fastq'.format(base_dir)
        self.ref_paired_fastq_file_name = '{}/tests/Mock_S280_L001_R2_001.fastq'.format(base_dir)
        self.ref_not_fastq_R1_file_name = '{}/tests/not_a_fastq_file_R1.fastq'.format(base_dir)
        self.ref_not_fastq_R2_file_name = '{}/tests/not_a_fastq_file_R2.fastq'.format(base_dir)
        self.ref_index_h1 = 'run mothur with a single button!'
        self.ref_submit_no_data_h2 = 'Parameters to run mothulity'
        self.ref_submit_data_submitted_h1 = '{} has been submitted'.format(submissiondata.job_name.replace('-', '_'))
        self.ref_status_h2 = '{} is {}'.format(submissiondata.job_name, self.test_job_status)
        self.ref_status_p = 'It means it is waiting for resources allocation on the computing cluster.'

    def test_index_response_code(self):
        """
        Tests whether response code of available urls equals <200>.
        """
        response = self.client.get(reverse("mothulity:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ref_index_h1)

    def test_single_file_upload(self):
        with open(self.ref_single_file_name) as fin:
            response = self.client.post(
                reverse("mothulity:index"),
                {'file_field': fin}
            )
        self.assertContains(response, views.upload_errors['uneven'])

    def test_bad_files_upload(self):
        with open(self.ref_not_fastq_R1_file_name) as fin_1:
            with open(self.ref_not_fastq_R2_file_name) as fin_2:
                response = self.client.post(
                    reverse("mothulity:index"),
                    {'file_field': (fin_1, fin_2)}
                )
        self.assertContains(response, views.upload_errors['format'])

    def test_good_files_upload_no_remote_dir_mounted(self):
        with open(self.ref_single_file_name) as fin_1:
            with open(self.ref_paired_fastq_file_name) as fin_2:
                response = self.client.post(
                    reverse("mothulity:index"),
                    {'file_field': (fin_1, fin_2)},
                    follow=True,
                )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, views.upload_errors['mothulity_fc'])

    @unittest.skipUnless(socket.gethostname() == hostname_production, 'Paths supposed to work on the production machine.')
    def test_good_files_upload_remote_dir_mounted(self):
        site = models.Site.objects.get(domain=self.settings_domain)
        path_settings = site.pathsettings
        path_settings.upload_path='/mnt/mothulity_HPC/jobs/'
        path_settings.hpc_prefix_path='/home/mothulity/jobs/'
        path_settings.save()
        with open(self.ref_single_file_name) as fin_1:
            with open(self.ref_paired_fastq_file_name) as fin_2:
                response = self.client.post(
                    reverse("mothulity:index"),
                    {'file_field': (fin_1, fin_2)},
                    follow=True,
                )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ref_submit_no_data_h2)

    @unittest.skipUnless(socket.gethostname() == hostname_development, 'Paths supposed to work on the development machine.')
    def test_good_files_upload_remote_dir_mounted(self):
        site = models.Site.objects.get(domain=self.settings_domain)
        path_settings = site.pathsettings
        path_settings.upload_path='/mnt/headnode/data/django/'
        path_settings.hpc_prefix_path='/home/dizak/data/django/'
        path_settings.save()
        with open(self.ref_single_file_name) as fin_1:
            with open(self.ref_paired_fastq_file_name) as fin_2:
                response = self.client.post(
                    reverse("mothulity:index"),
                    {'file_field': (fin_1, fin_2)},
                    follow=True,
                )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ref_submit_no_data_h2)


    def test_submit_no_data(self):
        response = self.client.post(
            reverse('mothulity:submit', args=(self.test_job_id,)),
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ref_submit_no_data_h2)

    def test_submit_data_submitted(self):
        response = self.client.post(
            reverse('mothulity:submit', args=(self.test_job_id,)),
            data=self.submission_data_dict,
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ref_submit_data_submitted_h1)

    def test_status_response_code(self):
        response = self.client.get(
            reverse('mothulity:status', args=(self.test_job_id,))
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ref_status_h2)
        self.assertContains(response, self.ref_status_p)

class ModelsTest(TestCase):
    """
    Tests for the models database API.
    """
    def setUp(self):
        """
        Sets up class level attrubutes for the tests.

        Parameters
        -------
        test_job_id: str
            UUID created ad hoc and converted into str.
        """
        self.test_job_id = str(uuid.uuid4())
        self.submission_data_dict = {"job_name": "test-job",
                                     "notify_email": "test@mail.com",
                                     "max_ambig": 0,
                                     "max_homop": 8,
                                     # "min_length": 100,
                                     # "max_length": 200,
                                     "min_overlap": 10,
                                     "screen_criteria": 95,
                                     "chop_length": 250,
                                     "precluster_diffs": 2,
                                     "classify_seqs_cutoff": 80,
                                     "amplicon_type": "16S"}
        self.test_seqs_count = 42
        self.test_job_status = "pending"
        self.test_submission_time = timezone.now()
        self.j_id = models.JobID(job_id=self.test_job_id)
        self.j_id.save()

    def test_job_id(self):
        """
        Tests whether job_id is properly saved and retrieved into and from the
        model.
        """
        self.assertIs(self.j_id.job_id, self.test_job_id)

    def test_seqsstats(self):
        """
        Tests whether job_id is properly saved and retrieved into and from the
        model as well as creation of seqsstats_set connected with the job_id.
        """
        stats = models.SeqsStats(job_id=self.j_id,
                                 seqs_count=self.test_seqs_count)
        stats.save()
        self.assertEqual(stats.seqs_count, self.test_seqs_count)

    def test_jobstatus(self):
        """
        Tests whether job_status and submission_time are properly saved and
        retrieved.
        """
        status = models.JobStatus(job_id=self.j_id,
                                  job_status=self.test_job_status,
                                  submission_time=self.test_submission_time)
        status.save()
        self.assertIs(status.job_status, self.test_job_status)
        self.assertIs(status.submission_time, self.test_submission_time)

    def test_submissiondata(self):
        """
        Tests whether job_name is properly sanitized - dashed replaced with
        underscores
        """
        submissiondata = models.SubmissionData(job_id=self.j_id,
                                               **self.submission_data_dict)
        submissiondata.save()
        self.assertIs(submissiondata.job_name, self.submission_data_dict["job_name"])


class FormsTest(TestCase):
    """
    Tests for the forms.
    """
    def setUp(self):
        """
        Sets up class level attrubutes for the tests.
        """
        self.form_data = {"job_name": "test-job",
                          "notify_email": "test@mail.com",
                          "max_ambig": 0,
                          "max_homop": 8,
                          # "min_length": 100,
                          # "max_length": 200,
                          "min_overlap": 10,
                          "screen_criteria": 95,
                          "chop_length": 250,
                          "precluster_diffs": 2,
                          "classify_seqs_cutoff": 80,
                          "amplicon_type": "16S"}
        self.clean_job_name = self.form_data["job_name"].replace("-", "_")

    def test_form_validity(self):
        form = forms.OptionsForm(self.form_data)
        self.assertTrue(form.is_valid())

    def test_form_sanitize(self):
        form = forms.OptionsForm(self.form_data)
        if form.is_valid():
            self.assertEqual(form.cleaned_data["job_name"], self.clean_job_name)
