import os

def download_fonts():
    # Define the input text file and output directory
    input_file = 'fontlinks.txt'
    output_directory = 'fonts/'

    # Create the output directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)

    # Read the lines from the input file
    with open(input_file, 'r') as file:
        lines = file.readlines()

    # Iterate through the lines and download the files
    for line in lines:
        name, link = line.strip().split('=')
        name = name.strip() + ".ttf"
        link = link.strip()
        
        # Check if the file already exists in the output directory
        if os.path.exists(os.path.join(output_directory, name)):
            print(f"File '{name}' already exists. Skipping download.")
        else:
            # Use wget to download the file with the specified name
            os.system(f'wget -O "{output_directory}/{name}" "{link}"')

    print("Downloads complete!")


if __name__ == "__main__":
    download_fonts()