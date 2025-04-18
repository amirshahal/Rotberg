import argparse
from common import p, log_args
import difflib
import os
import PyPDF2
import shutil


class CustomHelpFormatter(argparse.HelpFormatter):
    def _format_action(self, action):
        # Custom formatting for each action
        if action.help is not None and len(action.help) > 40:
            action_header = self._format_action_invocation(action)
            action_help_formatted = action.help.replace("\n", "\n" + ' ' * 24)
            return f"  {action_header}\n{' '*24}{action_help_formatted}"

        rv = super()._format_action(action)
        return rv


class ComparePdfs:
    def __init__(self):
        self.temp_unique_dir = None
        self.count = 0
        self.student_id2student_short_name = {}

    @staticmethod
    def remove_surrogate_pairs(text):
        """Remove surrogate pairs to avoid encoding issues."""
        return text.encode('utf-8', 'surrogatepass').decode('utf-8')

    def extract_text_from_pdf(self, pdf_path):
        text = ""
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                try:
                    page_text = page.extract_text()
                    # prev_page_text = page_text

                    if page_text:  # Only process if text is not None
                        clean_text = self.remove_surrogate_pairs(page_text)
                        text += clean_text + "\n"

                except UnicodeEncodeError:
                    # p(f"Failed to decode line from {pdf_path}, last decoded line is {prev_page_text}")
                    p(f"Failed to decode line from {pdf_path}")

        return text

    @staticmethod
    def longest_common_substring(text1, text2, n=3):
        # Split the text into words
        words1 = text1.split()
        words2 = text2.split()

        # Using a set to hold unique substrings found
        common_substrings = set()

        # Find the longest common substring using difflib
        seq_matcher = difflib.SequenceMatcher(None, words1, words2)
        # Find all matches
        for match in seq_matcher.get_matching_blocks():
            if match.size > 0:  # Only consider matches greater than zero
                common_substrings.add(' '.join(words1[match.a: match.a + match.size]))

        # Sort the common substrings by length, in descending order, and get the top n
        longest_common_substrings = sorted(common_substrings, key=len, reverse=True)[:n]

        return longest_common_substrings

    def compare_2_pdfs(self, file1, file2):
        f1 = os.path.basename(file1)
        f2 = os.path.basename(file2)

        self.count += 1
        p(f"#{self.count} Comparing {f1} and {f2}")
        # Extract text from both PDFs
        text1 = self.extract_text_from_pdf(file1)
        text2 = self.extract_text_from_pdf(file2)

        # Find the longest identical string of words
        longest_strings = self.longest_common_substring(text1, text2)
        # Print the results with word counts

        # print("The 3 longest identical strings of words and their word counts:")

        title = f"{f1}_{f2}"
        sub_title = ""

        msg = ""
        total_matched_count = 0
        for i, string in enumerate(longest_strings):
            count_matched = len(string.split())
            msg += f"'Identical string of words #{i +1} - Word Count: {count_matched}\n"
            msg += f"{string}\n"
            msg += "-----\n"
            msg += "\n"
            total_matched_count += count_matched
            sub_title += f"_{count_matched}"

        print(f"{title}_{total_matched_count}{sub_title}")
        print(msg)

    def run(self):
        if args.dir:
            self.temp_unique_dir = os.path.join(os.getcwd(), f'pdfs.{os.getpid()}')
            os.makedirs(self.temp_unique_dir)
            self.set_student_id_map()
            self.move_pdfs_to_dir(args.dir)
            self.compare_dir()
        else:
            self.compare_2_pdfs(args.file1, args.file2)

    def set_student_id_map(self):
        with open(args.student_mapping_csv_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    continue
                tokens = line.split(',')
                if len(tokens) < 3:
                    p(f"{args.student_mapping_csv_file} Found un expected line:\n{line}", True)
                self.student_id2student_short_name[tokens[0]] = tokens[2]

    def move_pdfs_to_dir(self, _dir):
        for file in os.listdir(_dir):
            full_file = os.path.join(_dir, file)
            if file.endswith('.pdf'):
                filename = self.get_short_filename(_dir)
                new_filename = os.path.join(self.temp_unique_dir, filename)
                if os.path.exists(new_filename):
                    p(f"Can NOT copy {full_file} to {new_filename}", True)
                shutil.copy(full_file, new_filename)
                p(f"Copied {full_file} to {new_filename}")

            if os.path.isdir(full_file):
                self.move_pdfs_to_dir(full_file)

    def get_short_filename(self, _dir):
        basename = os.path.basename(_dir)
        rv = None
        for student_id in self.student_id2student_short_name.keys():
            if student_id in basename:
                rv = f"{self.student_id2student_short_name[student_id]}.pdf"

        if rv is None:
            p(f"Can not find short name for {basename}", True)
        return rv

    def compare_dir(self):
        for file1 in sorted(os.listdir(self.temp_unique_dir)):
            full_file1 = os.path.join(self.temp_unique_dir, file1)
            if not full_file1.endswith('.pdf'):
                p(f"Found {full_file1} which is not pdf.", True)
            for file2 in sorted(os.listdir(self.temp_unique_dir)):
                full_file2 = os.path.join(self.temp_unique_dir, file2)
                if full_file2 > full_file1:
                    if not full_file2.endswith('.pdf'):
                        p(f"Found {full_file2} which is not pdf.", True)
                    self.compare_2_pdfs(full_file1, full_file2)


def read_args():
    # parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(formatter_class=CustomHelpFormatter)
    parser.add_argument('--dir')
    parser.add_argument('--file1')
    parser.add_argument('--file2')
    parser.add_argument('--verbose', action='store_true', default=False)
    parser.add_argument('--student_mapping_csv_file', required=True,
                        help="csv file with the following columns:]\nstudent_id,student_name,student_short_name\n\n"
                             "For example:\n"
                             "#student_id,student_name,student_short_name\n"
                             "152036,Omer Peri,OP\n"
                             "152037,Yonatan Pereg,YP\n"
                             "152038,Ori Abudi,OA\n\n"
                             "student_id should be the number assigned by Moodle for the student directory")

    _args = parser.parse_args()

    if not _args.dir and (not _args.file1 or not _args.file2):
        p("Please provide either dir or both file1 and file2", True)

    if not os.path.exists(_args.student_mapping_csv_file):
        p(f"student_mapping_csv_file {_args.student_mapping_csv_file} does not exist. "
          f"Please provide valid mapping file", True)

    log_args(_args)
    return _args


if __name__ == "__main__":
    args = read_args()
    compare_pdfs = ComparePdfs()
    compare_pdfs.run()
