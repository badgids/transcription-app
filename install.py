import platform
import subprocess
import sys

def download_pytorch(cuda=False):
    system = platform.system().lower()
    cuda_available = check_cuda_available()
    
    if cuda and cuda_available:
        if system == 'windows':
            index_url = 'https://download.pytorch.org/whl/cu{}'.format(get_cuda_version())
        elif system == 'linux':
            index_url = 'https://download.pytorch.org/whl/cu{}'.format(get_cuda_version())
        elif system == 'darwin':  # macOS
            print("CUDA is not available on macOS")
            return
        else:
            print("Unsupported operating system")
            return
    else:
        index_url = 'https://download.pytorch.org/whl/cpu/'

    try:
        subprocess.run(['pip', 'install', 'torch', 'torchvision', 'torchaudio', '--index-url', index_url], check=True)
    except subprocess.CalledProcessError as e:
        print("Error installing PyTorch:", e)
        return

def check_cuda_available():
    try:
        subprocess.run(['nvcc', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except FileNotFoundError:
        return False
    except subprocess.CalledProcessError:
        return False

def get_cuda_version():
    # Determine the CUDA version installed on the system
    # This is a simplified example, you may need to adjust it based on your system configuration
    return '121'  # Replace with the actual CUDA version

def main():
    cuda = input("Do you want to install PyTorch with CUDA support? (y/n): ").strip().lower()
    if cuda == 'y':
        cuda = True
    else:
        cuda = False

    download_pytorch(cuda)
    
    # After PyTorch installation, install the requirements.txt
    try:
        subprocess.run(['pip', 'install', '-r', 'requirements.txt'], check=True)
    except subprocess.CalledProcessError as e:
        print("Error installing requirements:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
