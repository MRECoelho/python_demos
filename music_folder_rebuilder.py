from mp3_tagger import MP3File, VERSION_2
import sys
import glob
import os
import string
from shutil import copy2

class Sanitizer:
    # simple object to preform sanitization of path names using
    # a whitelisting method so ensure folder hierarchy creation 
    _valid_chars = "-_.() {}{}".format(string.ascii_letters, string.digits)
    
    def sanitize(self, unsafe_str):
        return ''.join(c for c in unsafe_str if c in self._valid_chars)

def create_folder(path):
    try:
        os.mkdir(path)
    except OSError:
        print ("Creation of the directory {} failed".format(path))

if __name__ == "__main__":
    """ Small script that rebuilds my music folder hierarchy
        after deleting it. For all given recovered mp3 files in 
        input_path it checks the tag data and rebuilds it 
        according to the pattern: 
        <music> / <first letter artist> / <artist> / <year of album> - <album title>
        and afterwards copies the file to the previously defined destination.
    """        
    input_path = '.\\' if len(sys.argv) < 2 else sys.argv[1]
    output_path = '.\\output\\'  if len(sys.argv) < 3 else sys.argv[2]
    print ("Copying files from {} to {}".format(input_path, output_path))
    sanitizer = Sanitizer()

    for file_ in glob.glob("{}*.mp3".format(in_path)):
        mp3 = MP3File(file_)
        mp3.set_version(VERSION_2) # all files were mass encoded in version 2
        artist = sanitizer.sanitize(mp3.artist.strip())
        year = sanitizer.sanitize(mp3.year.strip())
        album = sanitizer.sanitize(mp3.album.strip())
        first_letter = artist[0]

        # to create some subfolder its ancestors must exist
        # thus check existance and otherwise create hierarchy
        # from path_list
        path_list = [output_path, first_letter, artist, '{} - {}'.format(year, album)]
        for i in range(2,5):
            path = os.path.join(*path_list[0:i])
            if not os.path.exists(path)
                create_folder(path_list)
            if i == 4:
                try:
                    copy2(f, path)
                    print("Copied file {} to directory {}".format(file_, path))
                except e:
                    print("Failed copying file {} to directory {}".format(file_, path))