import subprocess as sp
from glob import glob
import subprocess as sp
import os
from skbio.io import sniff
import Bio.SeqIO as sio
import math
from fnmatch import fnmatch
import pytz
import django
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from mothulity import models


class ParserError(Exception):
    """
    Inappropriate structure passed to parser.
    """
    pass


def write_file(input_file,
               path,
               chunk_size=8192):
    """
    Saves file from the forms.FileFieldForm to desired path in chunks.

    Parameters
    -------
    input_file: django.core.files.uploadedfile.UploadedFile
        File to be saved.
    path: str
        Path to file save.
    chunk: int, default <8192>
        Size of chunk the stream is divided to.
    """
    with open("/{}/{}".format(path, input_file), "wb+") as fout:
        for chunk in input_file.chunks(chunk_size=chunk_size):
            fout.write(chunk)


def chmod_file(input_file,
               mod=400):
    """
    Chmods file uploaded with forms.FileFieldForm. It is ment to prevent
    execution of uploaded files.

    Parameters
    -------
    input_file: str
        Path to input file.
    mod: int or str, default <400>
        Desired permissions of the input_file
    """
    sp.check_output("chmod {} {}".format(mod,
                                         input_file),
                    shell=True).decode('utf-8')


def convert_size(size_bytes):
    """
    Returns human-readable file size from input in bytes.

    Parameters
    -------
    size_bytes: int
        File size in bytes

    Returns
    -------
    int
        Size in human-readable format.
    """
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "{}{}".format(s, size_name[i])


def parse_sinfo(input_str,
                partition,
                state):
    """
    Parse sinfo command output and return desired information.

    Parameters
    -------
    input_str: str
        Output of the sinfo command.
    partition: str
        Partition of desired nodes.
    state: str
        State of desired nodes.

    Return
    -------
    int
        Number of nodes in desired state and partition.
    """
    s_line = [i for i in input_str.split("\n") if partition in i and state in i]
    if len(s_line) > 1:
        raise ParserError("""Found more than one line matching. Check if sinfo
              command output has not been changed.""")
    elif len(s_line) == 0:
        return None
    try:
        return int(s_line[0].split()[3])
    except IndexError:
        return None


def parse_squeue(input_str,
                 slurm_id,
                 key="ST"):
    """
    Parse squeue command output and return desired information.

    Parameters
    -------
    input_str: str
        Output of the squeue command.
    slurm_id: str or int
        slurm's ID of submitted job.
    key: str or int
        Desired value of squeue line to return

    Returns
    -------
    str or int
        Desired value of selected column and row from squeue command.
    None
        Returns None if record not found.
    """
    s_line = [i for i in input_str.split("\n") if str(slurm_id) in i]
    if len(s_line) > 1:
        raise ParserError("""Found more than one line matching. Check if squeue
              command output has not been changed.""")
    elif len(s_line) == 0:
        return None
    cols_vals = {"JOBID": int(s_line[0].split()[0]),
                 "PARTITION": str(s_line[0].split()[1]),
                 "NAME": str(s_line[0].split()[2]),
                 "USER": str(s_line[0].split()[3]),
                 "ST": str(s_line[0].split()[4]),
                 "TIME": str(s_line[0].split()[5]),
                 "NODES": int(s_line[0].split()[6])}
    if cols_vals["JOBID"] == int(slurm_id):
        return cols_vals[key]


def ssh_cmd(cmd,
            machine="headnode"):
    """
    Return output of remote command via ssh. Keys are obligatory!

    Parameters
    -------
    cmd: str
        Command to use.
    machine: str, default <headnode>
        Machine name on which command takes place.

    Return
    -------
    str
        Command output if cmd is fruitful function.
    """
    cmd = "ssh {} {}".format(machine, cmd)
    return sp.check_output(cmd, shell=True).decode('utf-8').strip()


def sniff_file(input_file,
               file_frmt="fastq"):
    """
    Returns bool depepending whether file validates as given type.

    Parameters
    -------
    input_file: str
        Path to input file.
    file_frmt: str, default <fastq>
        File type to be validated as.

    Returns
    ------
    bool
        True if file format matches desired file format or False if it does not.

    """
    try:
        if sniff(input_file)[0] == file_frmt:
            return True
    except Exception as e:
        return False


def count_seqs(input_files,
               file_format="fastq"):
    """
    Return number of all reads in the files.

    Parameters
    -------
    input_file: str
        Path to input files.
    file_format: str
        Format of input files.

    Returns
    -------
    int
        Sum of reads in input files.
    """
    input_glob = glob(input_files)
    seqs = [sio.parse(i,
                      file_format) for i in input_glob]
    return sum([len(list(i)) for i in seqs])


def render_moth_cmd(moth_exec="mothulity",
                    moth_files=None,
                    moth_opts=None,
                    shell="sbatch",
                    remove_spaces=True,
                    pop_elems=["id",
                               "job_id_id",
                               "amplicon_type"]):
    """
    Returns ready-to-go CLI command for mothulity from dict

    Parameters
    -------
    moth_exec: str, default <mothulity>
        Mothulity executable.
    moth_files: str, default <None>
        path/to/input/files.
    moth_opts: dict
        Dict of kvals converted to POSIX CLI optional arguments.
    remove_spaces: bool
        Replace whitespaces with underscores in job_name. Default <True>.

    Returns
    -------
    str
        POSIX mothulity command.
    """
    if remove_spaces is True:
        moth_opts["job_name"] = moth_opts["job_name"].replace(" ", "_")
    for i in pop_elems:
        moth_opts.pop(i)
    moth_opts["run"] = shell
    moth_opts["output-dir"] = moth_files
    moth_opt_str = " ".join(["--{} {}".format(k.replace("_", "-"), v)
                             for k, v in list(moth_opts.items())])
    return "{} {} {}".format(moth_exec,
                             moth_files,
                             moth_opt_str)


def get_pending_ids(ids_quantity=20,
                    status="pending",
                    status_model=models.JobStatus):
    """
    Returns Job IDs of oldest pending jobs within given limit retrieved from
    JobStatus model.

    Parameters
    -------
    ids_quantity: int, default <20>
        Maximium number of Job IDs to return.
    status: str, default <pending>
        Status of job in JobStatus model.
    status_model: django.models.Model, default JobStatus
        Django model to use.

    Returns
    -------
    list of str
        job_id with <pending> status.
    """
    ids = [i.job_id for i in status_model.objects.filter(job_status=status).
           order_by("-submission_time")]
    if len(ids) < ids_quantity:
        return ids
    else:
        return ids[:ids_quantity]


def get_ids_with_status(status="submitted",
                        status_model=models.JobStatus):
    """
    Returns Job IDs of jobs with given status.

    Parameters
    -------
    status: str, default <submitted>
        Status of job in JobStatus model.
    status_model: django.models.Model, default JobStatus
        Django model to use.

    Returns
    -------
    list of str
        job_id with <submitted> status.
    """
    return [i.job_id for i in status_model.objects.filter(job_status=status)]


def get_seqs_count(job_id):
    """
    Returns total sequence count retrieved from SeqsStats model.

    Parameters
    -------
    job_id: str
        Job ID by which sequece count is returned.

    Returns
    -------
    int
        Sequence count.
    """
    return models.JobID.objects.get(job_id=job_id).seqsstats.seqs_count


def get_slurm_id(job_id):
    """
    Returns slurm ID retrieved from JobStatus model.

    Parameters
    -------
    job_id: str
        Job ID by which sequece count is returned.

    Returns
    -------
    int
        slurm ID.
    """
    return models.JobID.objects.get(job_id=job_id).jobstatus.slurm_id


def get_retry(job_id):
    """
    Returns number of retry from JobStatus model.

    Parameters
    -------
    job_id: str
        Job ID by which sequece count is returned.

    Returns
    -------
    int
        Retry number.
    """
    return models.JobID.objects.get(job_id=job_id).jobstatus.retry


def queue_submit(job_id,
                 machine,
                 hpc_path,
                 sbatch_success="Submitted batch job"):
    """
    Retrieves required data from models by Job ID, renders mothulity command,
    copies files to computing cluster and sends the mothulity command. Adds
    JobStatus.slurm_id after slurm.

    Parameters
    -------
    job_id: str
        Job ID by which rest of data are retrieved.

    Returns
    -------
    bool
        <True> if SLURM status equals <R>.
    """
    job = models.JobID.objects.get(job_id=job_id)
    seqs_count = job.seqsstats.seqs_count
    sub_data = model_to_dict(job.submissiondata)
    job_id_dir = '{}{}/'.format(hpc_path, str(job_id).replace('-', '_'))
    # if seqs_count > 500000:
    #     sub_data["resources"] = "phi"
    # else:
    #     sub_data["resources"] = "n"
    sub_data["resources"] = "phi"
    print('Every job goes with resources=PHI. This is a temporary patch as there an unidentified problem with regular nodes.')
    moth_cmd = render_moth_cmd(moth_files=job_id_dir,
                                     moth_opts=sub_data,
                                     pop_elems=["job_id",
                                                "amplicon_type"])
    sbatch_out = ssh_cmd(
        cmd=moth_cmd,
        machine=machine,
        )
    if sbatch_success in sbatch_out:
        add_slurm_id(job_id=job_id,
                     slurm_id=int(sbatch_out.split(" ")[-1]))
        return True
    else:
        return False


def remove_except(directory,
                  pattern,
                  safety=True):
    """
    Remove non-recursively everything from the directory except pattern.

    Parameters
    -------
    directory: str
        Directory path from which the unwanted files will be removed.
    pattern: str
        Files ending with this will NOT be removed from the directory.
        If <None> or <False> - everything will be removed.
    """
    cmd = {True: 'ls', False: 'rm'}
    if not directory.endswith('/'):
        directory = directory + '/'
    files = glob('{}*'.format(directory))
    if not pattern:
        files_to_remove = files
    else:
        files_to_remove = [i for i in files if not fnmatch(i, pattern)]
    try:
        return sp.check_output(
            '{} {}'.format(cmd[safety], ' '.join(files_to_remove)),
            shell=True,
            ).decode('utf-8')
    except Exception as e:
        return False


def remove_dir(
    directory,
    safety=True,
):
    """
    Remove or list directory depending on safety switch.

    Parameters
    -------
    directory: str
        Directory path from which the unwanted files will be removed.
    safety: bool, default True
        Actual removal takes place only if the safety parameter is set to
        <False>. Otherwise it is just
    """
    cmd = {True: 'ls', False: 'rm'}
    option = {True: '-d', False: '-r'}
    try:
        return sp.check_output(
            '{} {} {}'.format(cmd[safety], option[safety], directory),
            shell=True
        ).decode('utf-8').split()
    except Exception as e:
        return False


def change_status(job_id,
                  new_status="submitted",
                  status_model=models.JobStatus):
    """
    Changes status from pending to submitted in the JobStatus model.

    Parameters
    -------
    job_id: str
        Job ID of job which status should be changed.
    new_status: str
        Content of new status.
    status_model: django.models.Model, default JobStatus
        Django model to use.
    """
    job = models.JobID.objects.get(job_id=job_id)
    job.jobstatus.job_status = new_status
    job.jobstatus.save()


def add_slurm_id(job_id,
                 slurm_id,
                 status_model=models.JobStatus):
    """
    Adds submission ID to the existing set in the JobStatus model.

    Parameters
    -------
    job_id: str
        Job ID of job which status should be changed.
    slurm_id: int
        Submission ID.
    status_model: django.models.Model, default JobStatus
        Django model to use.
    """
    job = models.JobID.objects.get(job_id=job_id)
    job.jobstatus.slurm_id = slurm_id
    job.jobstatus.save()


def add_retry(job_id,
              retry,
              status_model=models.JobStatus):
    """
    Adds retry existing set in the JobStatus model.

    Parameters
    -------
    job_id: str
        Job ID of job which status should be changed.
    retry: int
        Retry number.
    status_model: django.models.Model, default JobStatus
        Django model to use.
    """
    job = models.JobID.objects.get(job_id=job_id)
    job.jobstatus.retry = retry
    job.jobstatus.save()


def isrunning(job_id,
              machine,
              status_model=models.JobStatus,):
    """
    Check if job is actually running on the computing cluster.

    Parameters
    ------
    job_id: str
        Job ID of job which status should be changed.
    status_model: django.models.Model, default JobStatus
        Django model to use.

    Returns
    -------
    bool
        True is submitted ID has <R> state in squeue output.
    """
    slurm_id = get_slurm_id(job_id)
    if parse_squeue(ssh_cmd(cmd="squeue", machine=machine), slurm_id, "ST") == "R":
        return True
    else:
        return False


def isdone(directory,
           filename="analysis*zip"):
    """
    Check for the zipped analysis on the computing cluster and copy it back if
    it exists or return False otherwise.

    Parameters
    -------
    upld_dir: str
        Path to files on the computing cluster.

    Returns
    -------
    bool
        True if file exists or False if it does not.
    """
    try:
        sp.check_output(
            "ls {}{}".format(directory, filename),
            shell=True
            ).decode('utf-8')
        return True
    except Exception as e:
        return False


def isstale(
    input_file,
    expiry_time,
        ):
    """
    Check if file is older than given amount of time in seconds.
    """
    file_time =  pytz.datetime.datetime.fromtimestamp(os.path.getmtime(input_file))
    if file_time + pytz.datetime.timedelta(seconds=expiry_time) < pytz.datetime.datetime.now():
        return True
    else:
        return False


def get_dirs_without_ids(
    input_dir,
    dir2id={'_': '-'},
    job_model=models.JobID
    ):
    """
    Return list of directories which does not posses the JobID.

    Parameters
    -------
    input_dir: path
        Input path.
    status_model: django.models.Model, default JobID
        Django model to use.

    Returns
    -------
    list of str
        List of absolute paths to directories without JobID.
    """
    dir_char, job_id_char = tuple(dir2id.items())[0]
    input_dir_abs = os.path.abspath(input_dir)
    ids = [i.job_id for i in job_model.objects.all()]
    files_no_job_id = [i for i in os.listdir(input_dir_abs) if i.replace(dir_char, job_id_char) not in ids]
    dirs_no_job_id = [
        i
        for i in ['{}/{}/'.format(input_dir_abs, ii) for ii in files_no_job_id]
        if os.path.isdir(i)
        ]
    return dirs_no_job_id
