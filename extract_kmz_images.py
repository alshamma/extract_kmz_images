import zipfile
import os
import argparse
import xml.etree.ElementTree as ET
import shutil
import sys
import re
import tempfile

def sanitize_filename(name: str, max_length: int = 100) -> str:
    """Sanitize a filename by removing invalid characters and trimming length."""
    name = name.strip()  # Trim whitespace
    name = re.sub(r'[<>:"/\\|?*]', "", name)  # Remove invalid characters
    name = re.sub(r'\s+', "_", name)  # Replace spaces with underscores
    return name[:max_length]  # Truncate if too long

def extract_kmz(kmz_file: str, extract_dir: str) -> bool:
    """Extracts a KMZ file into a directory."""
    os.makedirs(extract_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(kmz_file, 'r') as kmz:
            kmz.extractall(extract_dir)
        return True
    except zipfile.BadZipFile:
        sys.stderr.write(f"Error: Invalid KMZ file.\n")
        return False

def parse_kml_for_images(kml_file: str) -> dict:
    """Parses a KML file and maps image filenames to placemark names."""
    if not os.path.exists(kml_file):
        sys.stderr.write(f"Error: KML file '{kml_file}' not found.\n")
        return {}

    namespace = {"kml": "http://www.opengis.net/kml/2.2"}

    try:
        tree = ET.parse(kml_file)
        root = tree.getroot()
    except ET.ParseError:
        sys.stderr.write(f"Error: Invalid or corrupted KML file.\n")
        return {}

    image_mapping = {}

    for placemark in root.findall(".//kml:Placemark", namespace):
        name_elem = placemark.find("kml:name", namespace)
        desc_elem = placemark.find("kml:description", namespace)
        name = name_elem.text if name_elem is not None else "Unnamed"
        name = sanitize_filename(name)

        # Find image references in description
        if desc_elem is not None and desc_elem.text:
            for line in desc_elem.text.split():
                if line.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp")):
                    image_mapping[line] = name  # Map filename to sanitized placemark name

        # Find image references in Schema
        for schema_data in placemark.findall(".//kml:SchemaData", namespace):
            for simple_data in schema_data.findall(".//kml:SimpleData", namespace):
                if simple_data.get("name") == "pdfmaps_photos" and simple_data.text:
                    # Extract filename from CDATA containing <img> element
                    match = re.search(r'<img[^>]+src="([^"]+)"', simple_data.text)
                    if match:
                        image_filename = match.group(1)
                        if image_filename.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp")):
                            image_mapping[image_filename] = name  # Map filename to sanitized placemark name

    return image_mapping

def get_unique_filename(directory: str, base_name: str, extension: str, suffix: str) -> str:
    """Generate a unique filename by appending a counter if needed."""
    base_name = f"{base_name}{suffix}" if suffix else base_name
    new_filename = f"{base_name}{extension}"
    counter = 1

    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base_name}_{counter}{extension}"
        counter += 1

    return new_filename

def rename_images(extract_dir: str, image_mapping: dict, suffix: str) -> None:
    """Renames extracted images based on sanitized KML tags with duplicate handling."""
    for image_file, placemark_name in image_mapping.items():
        original_path = os.path.join(extract_dir, image_file)
        if not os.path.exists(original_path):
            sys.stderr.write(f"Warning: Image '{image_file}' referenced in KML not found in KMZ.\n")
            continue

        base_name, extension = os.path.splitext(image_file)
        new_base_name = sanitize_filename(placemark_name)
        new_filename = get_unique_filename(extract_dir, new_base_name, extension, suffix)

        new_path = os.path.join(extract_dir, new_filename)
        shutil.move(original_path, new_path)
        print(f"Renamed: {image_file} -> {new_filename}")

def extract_images_from_kmz(kmz_path: str, output_dir: str, suffix: str) -> None:
    """Extracts images from a KMZ file and renames them based on sanitized KML tags."""
    temp_extract_dir = os.path.join(output_dir, "kmz_extract")

    if not extract_kmz(kmz_path, temp_extract_dir):
        return

    # Locate KML file
    kml_files = [f for f in os.listdir(temp_extract_dir) if f.endswith(".kml")]
    if not kml_files:
        sys.stderr.write("Error: No KML file found in KMZ.\n")
        return

    kml_file = os.path.join(temp_extract_dir, kml_files[0])
    image_mapping = parse_kml_for_images(kml_file)

    if not image_mapping:
        sys.stderr.write("Warning: No images found in KML description fields.\n")

    rename_images(temp_extract_dir, image_mapping, suffix)

    print(f"Images extracted and renamed in: {temp_extract_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract and rename images from a KMZ file.")
    parser.add_argument("kmz_file", nargs="?", help="Path to the KMZ file (or read from stdin)")
    parser.add_argument("output_dir", help="Directory to save extracted images")
    parser.add_argument("-s", "--suffix", default="", help="String to append to the base filename")

    args = parser.parse_args()

    if args.kmz_file is None and sys.stdin.isatty():
        sys.stderr.write("Error: Missing KMZ file or output_dir. Provide a file path or use stdin and be sure to provide an output directory.\n")
        sys.exit(1)

    if args.output_dir is None:
        sys.stderr.write("Error: Missing output directory.\n")
        sys.exit(1)

    if args.kmz_file:
        if not os.path.isfile(args.kmz_file):
            sys.stderr.write("Error: Missing KMZ file -- it was not found.\n")
            sys.exit(1)

        extract_images_from_kmz(args.kmz_file, args.output_dir, args.suffix)
    else:
        # Read KMZ from stdin and save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".kmz") as temp_kmz:
            temp_kmz.write(sys.stdin.buffer.read())
            temp_kmz_path = temp_kmz.name

        try:
            extract_images_from_kmz(temp_kmz_path, args.output_dir, args.suffix)
        finally:
            os.remove(temp_kmz_path)  # Cleanup
