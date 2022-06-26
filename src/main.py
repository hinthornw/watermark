"""Main entrypoint."""
import argparse
import io
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from PyPDF2 import PdfFileReader, PdfFileWriter
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import inch, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from tqdm import tqdm

_DIR = Path(__file__).parent
with (_DIR / "prefix.txt").open("r") as f:
    _PREFIX = f.read()
with (_DIR / "suffix.txt").open("r") as f:
    _SUFFIX = f.read()

_TILT_DEGREES = 30


def get_style() -> ParagraphStyle:
    """Return the style."""
    stylesheet = getSampleStyleSheet()
    normalStyle: ParagraphStyle = stylesheet["Normal"]
    normalStyle.fontSize = 14
    normalStyle.fontName = "Helvetica"
    normalStyle.alignment = TA_CENTER
    # Set opacity for watermark
    normalStyle.textColor = (0, 0, 0, 0.5)
    return normalStyle


def get_date() -> str:
    """Return the date."""
    return datetime.now().strftime("%m-%d-%Y")


def write_paragraph(
    canvas: canvas.Canvas,
    text: str,
    x: int,
    y: int,
    font_size: Optional[int] = None,
) -> None:
    """Write a paragraph."""
    style = get_style()
    if font_size is not None:
        style.fontSize = font_size
    paragraph = Paragraph(text, style)
    paragraph.wrap(inch * 4, inch * 4)
    canvas.rotate(_TILT_DEGREES)
    paragraph.drawOn(canvas, x, y)
    canvas.rotate(-_TILT_DEGREES)


def create_pdf(person: str) -> None:
    """Create a PDF file."""
    current_date = get_date()
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # Draw the text in the top left hand of the page.
    # Origin (0, 0) is the bottom left of the page.
    # Since we rotate, the X value has to be larger.

    # Value that centers it after rotating 45 degrees
    X_VAL = inch * 4.5
    MAX_Y = inch * 7.5
    write_paragraph(can, _PREFIX, X_VAL, MAX_Y - (1.5 * inch))
    # Create the center text
    write_paragraph(can, person, X_VAL, MAX_Y - (4 * inch))
    # Create the center text
    write_paragraph(
        can,
        current_date,
        X_VAL,
        MAX_Y - (4.2 * inch),
    )
    # Create the Suffix
    write_paragraph(can, _SUFFIX, X_VAL, 0)
    can.save()
    # move to the beginning of the StringIO buffer
    packet.seek(0)
    # create a new PDF with Reportlab
    new_pdf = PdfFileReader(packet)
    return new_pdf.getPage(0)


def get_args(argsrc: Optional[List[str]] = None) -> argparse.Namespace:
    """Return args."""
    parser = argparse.ArgumentParser(description="Automating PDF watermarking.")
    parser.add_argument("input", type=Path, help="Input PDF file.")
    parser.add_argument("output", type=Path, help="Output PDF file.")
    parser.add_argument("--names", nargs="+", required=False, help="People's Names.")
    parser.add_argument(
        "--name-file",
        type=Path,
        required=False,
        help="Path to file containing people's names.",
    )
    if argsrc is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(argsrc)
    return args


def watermark_pdf(input_path: Path, person: str, output_path: Path) -> None:
    """Read input and watermark paths, merge, then write to output_path."""
    pdf_writer = PdfFileWriter()
    with input_path.open("rb") as inp_f:
        # read content of the original file
        pdf = PdfFileReader(inp_f)
        input_pages = [page for page in pdf.pages]
        watermark = create_pdf(person)
        # Iterate through all pages of the original PDF
        # And add the watermark to each page
        for page in input_pages:
            # page = pdf.getPage(page_num)
            # merge the two pages
            page.mergePage(watermark)
            # add page
            pdf_writer.addPage(page)

        with output_path.open("wb") as filehandle_output:
            # write the watermarked file to the new file
            pdf_writer.write(filehandle_output)


def combine_output_name_and_person(output_path: Path, person: str) -> Path:
    """Combine output name and person."""
    return (
        output_path.parent
        / f"{output_path.stem}_{person.replace(' ', '_')}_{get_date()}.pdf"
    )


def main(args: Optional[argparse.Namespace] = None) -> None:
    """Main entrypoint."""
    if args is None:
        args = get_args()
    if not args.input.exists():
        raise FileNotFoundError(f"{args.input} does not exist.")
    if args.names is not None:
        people = args.names
        for person in tqdm(people):
            output_file = combine_output_name_and_person(args.output, person)
            watermark_pdf(args.input, person, output_file)
    elif args.name_file is not None:
        with args.name_file.open("r") as f:
            people = f.read().splitlines()
        for person in tqdm(people):
            output_file = combine_output_name_and_person(args.output, person)
            watermark_pdf(args.input, person, output_file)
    else:
        raise ValueError("No names provided.")


if __name__ == "__main__":
    main()
