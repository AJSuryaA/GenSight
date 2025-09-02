import os
import shutil
import subprocess
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form

from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


from app.backend.workflows.etl.pandas_processing import get_dataset_info as get_pandas_info
from app.backend.workflows.etl.pyspark_processing import get_dataset_info as get_pyspark_info

from app.backend.workflows.eda.pandas_eda import pandas_eda
from app.backend.workflows.eda.pyspark_eda import pyspark_eda
import pandas as pd
from pyspark.sql import SparkSession

from app.backend.workflows.eda.pandas_profiling_eda import generate_pandas_eda_report

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: run before app starts receiving requests
    ensure_hadoop_running()

    yield

    # Shutdown: run after app stops receiving requests (optional cleanup)
    # Put any cleanup code here if needed


app = FastAPI(lifespan=lifespan)

# Paths for frontend files (adjust if needed)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "../frontend")
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "templates")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

# Directory to save uploaded files temporarily before moving to data lake
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../../uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/reports", StaticFiles(directory="app/backend/workflows/eda/reports"), name="reports")

# Serve the upload page
@app.get("/")
async def read_index():
    return FileResponse(os.path.join(TEMPLATES_DIR, "index.html"))

def check_hadoop_running():
    try:
        result = subprocess.run(['jps'], capture_output=True, text=True)
        running_services = [line.split()[1] for line in result.stdout.strip().split('\n') if len(line.split()) > 1]

        required_services = ['NameNode', 'DataNode', 'ResourceManager', 'NodeManager']
        missing_services = [service for service in required_services if service not in running_services]

        if missing_services:
            print(f"Missing Hadoop services: {missing_services}")
            return False
        print("All essential Hadoop services are running.")
        return True
    except Exception as e:
        print(f"Error checking Hadoop services: {e}")
        return False


def start_hadoop_services():
    try:
        # Replace with your actual Hadoop sbin path
        hadoop_home = os.environ.get('HADOOP_HOME')
        hadoop_sbin_path = f'{hadoop_home}/sbin'
        subprocess.run(['bash', f'{hadoop_sbin_path}/start-dfs.sh'], check=True)
        subprocess.run(['bash', f'{hadoop_sbin_path}/start-yarn.sh'], check=True)
        print("Hadoop DFS and YARN started successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to start Hadoop services: {e}")


def ensure_hadoop_running():
    if not check_hadoop_running():
        print("Hadoop services not running. Starting services...")
        start_hadoop_services()
    else:
        print("Hadoop services already running.")

def choose_processing_mode(file_path, command_input=None):
    SIZE_THRESHOLD = 100 * 1024 * 1024  # 100MB
    if command_input:
        if command_input.strip() == "-f:p":
            return "pandas"
        elif command_input.strip() == "-f:ps":
            return "pyspark"

    file_size = os.path.getsize(file_path)
    if file_size <= SIZE_THRESHOLD:
        return "pandas"
    else:
        return "pyspark"

def upload_to_hdfs(local_file_path, hdfs_dir="/user/gen_sight/uploads"):
    try:
        subprocess.run(["hdfs", "dfs", "-mkdir", "-p", hdfs_dir], check=True)
        result = subprocess.run(
            ["hdfs", "dfs", "-put", "-f", local_file_path, hdfs_dir],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return os.path.join(hdfs_dir, os.path.basename(local_file_path))
    except subprocess.CalledProcessError as e:
        print(f"Error uploading to HDFS: {e.stderr}")
        raise


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), command: str = Form(None)):
    try:
        
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        await file.close()

        # Determine processing mode
        mode = choose_processing_mode(file_location, command)

        # Upload to HDFS
        hdfs_path = upload_to_hdfs(file_location)

        # Get dataset info based on processing mode
        if mode == "pandas":
            dataset_info = get_pandas_info(file_location)

            # Run EDA for pandas
            df = pd.read_csv(file_location)
            report_file = generate_pandas_eda_report(df)
            report_url = report_file.replace("app/backend", "app/backend/workflows/eda/reports")  # Adjust path for URL
            pandas_eda(df)
            return JSONResponse({
                # other fields...
                "eda_report_url": report_url
            })
            

        elif mode == "pyspark":
            dataset_info = get_pyspark_info(hdfs_path)

            # Run EDA for pyspark
            spark = SparkSession.builder.appName("EDA").getOrCreate()
            sdf = spark.read.csv(hdfs_path, header=True, inferSchema=True)
            pyspark_eda(sdf)
            spark.stop()
            
        else:
            dataset_info = {}

        return JSONResponse({
            "filename": file.filename,
            "processing_mode": mode,
            "message": "File uploaded successfully.",
            "local_path": file_location,
            "hdfs_path": hdfs_path,
            "dataset_info": dataset_info
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})