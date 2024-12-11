import os
import boto3
import yaml
import numpy as np
import cv2
from io import BytesIO

def load_class_names_from_s3(s3_bucket_name: str, yaml_s3_uri: str):
    """
    Load class names from the YOLO data.yaml file stored on S3.
    
    Args:
        s3_bucket_name (str): The S3 bucket name where the data.yaml is stored.
        yaml_s3_uri (str): The S3 URI for the data.yaml file.
    
    Returns:
        list: List of class names.
    """
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv("ACCESS_KEY"),
        aws_secret_access_key=os.getenv("SECRET_KEY"),
        region_name=os.getenv("REGION_NAME")
    )

    try:
        # Extract the key from the S3 URI (remove 's3://<bucket_name>/' part)
        key = yaml_s3_uri.replace(f"s3://{s3_bucket_name}/", "")
        
        # Get the data.yaml file from S3
        yaml_obj = s3.get_object(Bucket=s3_bucket_name, Key=key)
        yaml_data = yaml_obj['Body'].read().decode("utf-8")
        
        # Parse the YAML content
        data = yaml.safe_load(yaml_data)
        
        return data['names']  # Return the list of class names from the 'names' field
    
    except Exception as e:
        print(f"Error loading YAML file from S3: {e}")
        return []

def lambda_handler(event, context):
    """
    Lambda handler to process images and annotations from S3 and upload preview images.
    
    Args:
        event (dict): Event data passed to the Lambda function (could contain parameters such as S3 bucket names).
        context (object): Lambda context object containing runtime information.
    """

    s3_bucket_name = "flipkartdataset1"
    image_folder = "train/images"
    labels_folder = "train/labels"
    preview_bucket_name = "flipkartprocessedpreview" 
    yaml_s3_uri = "s3://flipkartdataset1/data.yaml"  
    num_frames = 10

    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv("ACCESS_KEY"),
        aws_secret_access_key=os.getenv("SECRET_KEY"),
        region_name=os.getenv("REGION_NAME")
    )

    # Load class names from the data.yaml file stored in S3
    class_names = load_class_names_from_s3(s3_bucket_name, yaml_s3_uri)

    # List all files in the image folder
    image_objects = s3.list_objects_v2(Bucket=s3_bucket_name, Prefix=image_folder)
    if 'Contents' not in image_objects:
        print(f"Error: No images found in the folder {image_folder} in the S3 bucket.")
        return

    # Sort images by last modified time (S3 object metadata)
    image_objects['Contents'].sort(key=lambda x: x['LastModified'], reverse=True)

    # Calculate the number of frames to process (take the minimum of available images and num_frames)
    available_frames = min(len(image_objects['Contents']), num_frames)

    # Process the latest `available_frames` images
    for i, image_object in enumerate(image_objects['Contents'][:available_frames]):
        image_file = image_object['Key']
        if image_file.endswith(".jpg"):  # Process only .jpg files
            frame_name = os.path.splitext(os.path.basename(image_file))[0]  # Extract frame name without extension
            annotation_file = os.path.join(labels_folder, f"{frame_name}.txt")

            # Download the image and annotation files from S3
            try:
                image_obj = s3.get_object(Bucket=s3_bucket_name, Key=image_file)
                annotation_obj = s3.get_object(Bucket=s3_bucket_name, Key=annotation_file)

                # Load the image into memory
                image_data = image_obj['Body'].read()
                image_np = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

                # Read and parse the annotations
                annotation_data = annotation_obj['Body'].read().decode("utf-8").splitlines()

                img_height, img_width, _ = image.shape

                image2 = cv2.resize(image, (640, 640))
                # Process each annotation and draw bounding boxes
                for annotation in annotation_data:
                    # YOLO format: class_id x_center y_center width height
                    data = annotation.strip().split()
                    class_id, x_center, y_center, bbox_width, bbox_height = map(float, data)

                    # Convert class_id to object name
                    object_name = class_names[int(class_id)] if 0 <= int(class_id) < len(class_names) else "Unknown"

                    # Convert normalized coordinates to pixel values
                    x_min = int((x_center - bbox_width / 2) * img_width)
                    y_min = int((y_center - bbox_height / 2) * img_height)
                    x_max = int((x_center + bbox_width / 2) * img_width)
                    y_max = int((y_center + bbox_height / 2) * img_height)

                    # Draw the bounding box on the image
                    cv2.rectangle(image2, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                    cv2.putText(image2, object_name, 
                                (x_min, y_min - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 
                                0.5, (0, 255, 0), 2)

                # Save the image with bounding boxes locally (in memory)
                _, encoded_image = cv2.imencode('.jpg', image2)
                preview_image_bytes = BytesIO(encoded_image.tobytes())

                # Upload the preview image to the preview S3 bucket
                s3.upload_fileobj(preview_image_bytes, preview_bucket_name, f"previews/{frame_name}_preview.jpg")

            except Exception as e:
                print(f"Error processing frame {frame_name}: {e}")
                continue

    return {
        'statusCode': 200,
        'body': f'Processing completed successfully for {available_frames} images.'
    }
