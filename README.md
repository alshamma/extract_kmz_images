# KMZ Image Extractor

## Overview
This Python script extracts images from a KMZ file and renames them based on the corresponding placemark names in the KML file. It ensures that filenames are sanitized, handles duplicate names, and allows an optional suffix to be appended to the filenames.

## Features
- Extracts images from a KMZ file
- Renames images based on placemark names in the KML file
- Ensures filenames are valid for the operating system
- Reports errors (e.g., missing files, invalid KML) to `stderr`
- Handles duplicate image names by appending a number
- Supports reading KMZ from `stdin`
- Allows an optional suffix using `-s` or `--suffix`

## Requirements
- Python 3.12.4

## Installation
No installation required. Just download the script and run it with Python.

## Usage
### Extract images from a KMZ file:
```sh
python extract_kmz_images.py myfile.kmz extracted_images/
```

### Read KMZ from stdin:
```sh
cat myfile.kmz | python extract_kmz_images.py - extracted_images/
```

### Append a suffix to filenames:
```sh
python extract_kmz_images.py myfile.kmz extracted_images/ -s "_trip"
```

## Example Output
```
Renamed: image1.jpg -> Mountain_View_trip.jpg
Renamed: image2.jpg -> Lake_trip.jpg
Renamed: image3.jpg -> Lake_trip_1.jpg
Warning: Image 'missing.jpg' referenced in KML not found in KMZ.
Images extracted and renamed in: extracted_images/kmz_extract
```

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributing
Pull requests are welcome! If you find a bug or have a feature request, please open an issue.

## Author
Nabeel Al-Shamma

Original program generated using ChatGPT
