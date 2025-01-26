import fitz  # PyMuPDF
import argparse
import os

MAX_FILE_SIZE_MB = 4.3
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024  # 5 MB in bytes


def save_large_pdf(images, output_pdf):
    """
    Save all images into a single PDF.

    Args:
        images (list): List of image file paths.
        output_pdf (str): Path to save the combined PDF.
    """
    doc = fitz.open()  # Create a new PDF
    for image_path in images:
        try:
            img = fitz.open(image_path)  # Open the image
            pdfbytes = img.convert_to_pdf()  # Convert image to a PDF page
            img_pdf = fitz.open("pdf", pdfbytes)
            doc.insert_pdf(img_pdf)  # Add the page to the main document
        except Exception as e:
            print(f"Error converting {image_path} to PDF: {e}")
            continue

    if doc.page_count > 0:
        try:
            doc.save(output_pdf)
            print(f"Combined PDF saved as: {output_pdf}")
        except Exception as e:
            print(f"Error saving combined PDF {output_pdf}: {e}")
    else:
        print("No pages added to the PDF. Check if images were converted successfully.")


def split_pdf(input_pdf, output_folder):
    """
    Split a PDF into smaller PDFs, each smaller than 5 MB.

    Args:
        input_pdf (str): Path to the input PDF.
        output_folder (str): Folder to save the split PDFs.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    try:
        pdf_document = fitz.open(input_pdf)
        print(f"Opened PDF with {len(pdf_document)} pages.")
    except Exception as e:
        print(f"Error opening PDF {input_pdf}: {e}")
        return

    current_pdf = fitz.open()
    split_index = 1

    for page_number in range(len(pdf_document)):
        try:
            current_pdf.insert_pdf(pdf_document, from_page=page_number, to_page=page_number)

            # Save the current PDF if it exceeds the 5MB limit
            temp_split_pdf_path = os.path.join(output_folder, f"split_{split_index}.pdf")
            current_pdf.save(temp_split_pdf_path)

            current_size = os.path.getsize(temp_split_pdf_path)
            print(f"Added page {page_number + 1} to split_{split_index}.pdf. Current size: {current_size / (1024 * 1024):.2f} MB")

            # If the current split PDF exceeds 5MB, start a new split file
            if current_size >= MAX_FILE_SIZE_BYTES:
                print(f"Split PDF exceeds {MAX_FILE_SIZE_MB} MB, starting a new file.")
                split_index += 1
                current_pdf = fitz.open()  # Create a new PDF for the next part

        except Exception as e:
            print(f"Error processing page {page_number + 1}: {e}")

    # Final check to ensure the last PDF is saved
    if current_pdf.page_count > 0:
        try:
            temp_split_pdf_path = os.path.join(output_folder, f"split_{split_index}.pdf")
            current_pdf.save(temp_split_pdf_path)
            print(f"Final split PDF saved as: {temp_split_pdf_path}")
        except Exception as e:
            print(f"Error saving final split PDF: {e}")


def pdf_to_split_pdfs(input_pdf, temp_pdf, output_folder):
    """
    Converts a PDF into a single large PDF of JPEG-rendered pages and splits it into smaller PDFs.

    Args:
        input_pdf (str): Path to the input PDF.
        temp_pdf (str): Path to save the intermediate large PDF.
        output_folder (str): Folder to save the split PDFs.
    """
    temp_images = []  # Store temporary image paths

    try:
        # Open the input PDF
        pdf_document = fitz.open(input_pdf)

        # Render each page as a temporary JPEG image
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            pix = page.get_pixmap(dpi=150)  # Create a Pixmap (image)
            temp_image_path = f"temp_page_{page_num + 1}.jpg"
            pix.save(temp_image_path)  # Save the Pixmap as a JPEG
            temp_images.append(temp_image_path)
            print(f"Page {page_num + 1} rendered to {temp_image_path}")

        # Combine all images into a single large PDF
        save_large_pdf(temp_images, temp_pdf)

        # Check if the large PDF was successfully created before proceeding to split
        if os.path.exists(temp_pdf):
            print(f"Large PDF created successfully: {temp_pdf}")
            # Split the large PDF into smaller PDFs
            split_pdf(temp_pdf, output_folder)
        else:
            print(f"Error: The large PDF was not created: {temp_pdf}")

    except Exception as e:
        print(f"An error occurred during processing: {e}")
    finally:
        # Clean up temporary images
        for temp_image in temp_images:
            if os.path.exists(temp_image):
                os.remove(temp_image)
        # Remove the temporary large PDF
        if os.path.exists(temp_pdf):
            os.remove(temp_pdf)


def main():
    parser = argparse.ArgumentParser(
        description="Convert a PDF into a single large PDF of JPEG-rendered pages and then split it into smaller PDFs."
    )
    parser.add_argument("input_pdf", help="Path to the input PDF file.")
    parser.add_argument(
        "--output_folder",
        default="split_pdfs",
        help="Folder to save the split PDFs (default: split_pdfs).",
    )
    parser.add_argument(
        "--temp_pdf",
        default="temp_large.pdf",
        help="Path to save the intermediate large PDF (default: temp_large.pdf).",
    )
    args = parser.parse_args()

    try:
        pdf_to_split_pdfs(args.input_pdf, args.temp_pdf, args.output_folder)
    except FileNotFoundError:
        print(f"Error: File '{args.input_pdf}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
