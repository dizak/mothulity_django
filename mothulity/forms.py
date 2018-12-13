from django import forms
from . import utils

input_class = "w3-input"


class FileFieldForm(forms.Form):
    """
    Form for multiple files upload.
    """
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True,
                                                                        "class": input_class,
                                                                        "autocomplete": "off"}))

    # def clean_file_field(self):
    #     max_size = 104857600
    #     cleaned_data = self.cleaned_data["file_field"]
    #     if cleaned_data.size > max_size:
    #         size_hr = utils.convert_size(cleaned_data._size)
    #         max_size_hr = utils.convert_size(max_size)
    #         msg = "File too big ({}). Maximumum size allowed: {}".format(size_hr,
    #                                                                      max_size_hr)
    #         self.add_error("file_field", msg)
    #     return cleaned_data


class OptionsForm(forms.Form):
    """
    Form for specifying analysis options and parameters.
    """
    job_name = forms.CharField(label="Name of your job. It will be displayed\
                               in the results.",
                               max_length=20,
                               error_messages={"required": ""},
                               widget=forms.
                               TextInput(attrs={"value": "",
                                                "class": input_class}))
    notify_email = forms.EmailField(label="e-mail address on which you will be\
                                    notified",
                                    max_length=40,
                                    widget=forms.
                                    EmailInput(attrs={"value": "",
                                                      "class": input_class}))
    max_ambig = forms.IntegerField(label="Maximum number of ambiguous bases\
                                   allowed.",
                                   widget=forms.
                                   TextInput(attrs={"value": 0,
                                                    "class": input_class}))
    max_homop = forms.IntegerField(label="Maximum number of homopolymers\
                                   allowed.",
                                   widget=forms.
                                   TextInput(attrs={"value": 8,
                                                    "class": input_class}))
    # min_length = forms.IntegerField(label="Minimum length of read allowed.",
    #                                 widget=forms.
    #                                 TextInput(attrs={"value": 100,
    #                                                  "class": input_class}))
    # max_length = forms.IntegerField(label="Maximum length of read allowed.",
    #                                 widget=forms.
    #                                 TextInput(attrs={"value": 300,
    #                                                  "class": input_class}))
    min_overlap = forms.IntegerField(label="Minimum number of bases overlap in\
                                     contig",
                                     widget=forms.
                                     TextInput(attrs={"value": 10,
                                                      "class": input_class}))
    screen_criteria = forms.IntegerField(label="Trim start and end of the read\
                                         will be selected to fit these values\
                                         of that percentage of all reads",
                                         widget=forms.
                                         TextInput(attrs={"value": 95,
                                                          "class": input_class}))
    chop_length = forms.IntegerField(label=" Cut all the reads to this length.\
                                     Keeps front of the sequences. Applies to\
                                     ITS only!",
                                     widget=forms.
                                     TextInput(attrs={"value": 120,
                                                      "class": input_class}))
    precluster_diffs = forms.IntegerField(label="Number of differences between\
                                          reads treated as insignificant.",
                                          widget=forms.
                                          TextInput(attrs={"value": 2,
                                                           "class": input_class}))
    classify_seqs_cutoff = forms.IntegerField(label="Bootstrap value for taxonomic\
                                              assignment. Minimum value of\
                                              read similarity to database when\
                                              performing taxonomic assignment.",
                                              widget=forms.
                                              TextInput(attrs={"value": 80,
                                                               "class": input_class}))
    amplicon_type = forms.ChoiceField(label="Amplicon type.",
                                      choices=[("16S", "16S"),
                                               ("ITS", "ITS")],
                                      widget=forms.
                                      RadioSelect())

    # def clean(self):
    #     """
    #     Validates if min_length is not greater than max_length. Passes proper
    #     information to OptionsForm._errors and deletes value from
    #     OptionsForm.cleaned_data.
    #     """
    #     cleaned_data = super(OptionsForm, self).clean()
    #     min_length = cleaned_data.get("min_length")
    #     max_length = cleaned_data.get("max_length")
    #     if min_length >= max_length:
    #         msg = "Minimum length cannot be greater or qual to minimum length"
    #         self.add_error("min_length", msg)
    #         self.add_error("max_length", msg)

    def clean_job_name(self):
        """
        Replace non-alphanumeric chars with underscores in job_name.
        """
        cleaned_data = self.cleaned_data["job_name"]
        return "".join([i if i.isalnum() else "_" for i in cleaned_data])

    def clean_max_ambig(self):
        """
        Add error if negative values is passed.
        """
        cleaned_data = self.cleaned_data["max_ambig"]
        if cleaned_data < 0:
            msg = "Pass non-negative values"
            self.add_error("max_ambig", msg)
        return cleaned_data

    def clean_max_homop(self):
        """
        Add error if negative values is passed.
        """
        cleaned_data = self.cleaned_data["max_homop"]
        if cleaned_data < 0:
            msg = "Pass non-negative values"
            self.add_error("max_homop", msg)
        return cleaned_data

    # def clean_min_length(self):
    #     """
    #     Add error if negative values is passed.
    #     """
    #     cleaned_data = self.cleaned_data["min_length"]
    #     if cleaned_data < 0:
    #         msg = "Pass non-negative values"
    #         self.add_error("min_length", msg)
    #     return cleaned_data
    #
    # def clean_max_length(self):
    #     """
    #     Add error if negative values is passed.
    #     """
    #     cleaned_data = self.cleaned_data["max_length"]
    #     if cleaned_data < 0:
    #         msg = "Pass non-negative values"
    #         self.add_error("max_length", msg)
    #     return cleaned_data

    def clean_min_overlap(self):
        """
        Add error if negative values is passed.
        """
        cleaned_data = self.cleaned_data["min_overlap"]
        if cleaned_data < 0:
            msg = "Pass non-negative values"
            self.add_error("min_overlap", msg)
        return cleaned_data

    def clean_screen_criteria(self):
        """
        Add error if negative values is passed.
        """
        cleaned_data = self.cleaned_data["screen_criteria"]
        if cleaned_data < 0:
            msg = "Pass non-negative values"
            self.add_error("screen_criteria", msg)
        return cleaned_data

    def clean_chop_length(self):
        """
        Add error if negative values is passed.
        """
        cleaned_data = self.cleaned_data["chop_length"]
        if cleaned_data < 0:
            msg = "Pass non-negative values"
            self.add_error("chop_length", msg)
        return cleaned_data

    def clean_precluster_diffs(self):
        """
        Add error if negative values is passed.
        """
        cleaned_data = self.cleaned_data["precluster_diffs"]
        if cleaned_data < 0:
            msg = "Pass non-negative values"
            self.add_error("precluster_diffs", msg)
        return cleaned_data

    def clean_classify_seqs_cutoff(self):
        """
        Add error if negative values is passed.
        """
        cleaned_data = self.cleaned_data["classify_seqs_cutoff"]
        if cleaned_data < 0:
            msg = "Pass non-negative values"
            self.add_error("classify_seqs_cutoff", msg)
        elif cleaned_data > 100:
            msg = "Pass below 100 value"
            self.add_error("classify_seqs_cutoff", msg)
        return cleaned_data


class ResendResultsEMailForm(forms.Form):
    """
    Form for specifying e-mail address for re-sending the results.
    """
    email_address = forms.EmailField(
        label='e-mail address for re-sending the results:',
        max_length=40,
        widget=forms.EmailInput(attrs={'value': '', 'class': input_class})
    )
