# README: Lambda Function for Image Preview Creation and Upload

## Overview

This AWS Lambda function is designed to process the latest modified images from an S3 bucket, generate preview images by drawing bounding boxes on objects based on YOLOv11 annotations, and upload the processed preview images to another S3 bucket. The function works by fetching the latest modified images, applying YOLO annotations, and creating preview images to be stored in a specified destination bucket.

### Key Features:
- **Process Latest Modified Images**: The function automatically identifies and processes the most recently modified images in a specified S3 bucket.
- **YOLOv11 Annotation Parsing**: It parses YOLOv11 formatted annotations to draw bounding boxes around objects in the images.
- **Generate Preview Images**: The function resizes the images to 640x640 and draws bounding boxes with class names.
- **Upload Preview to S3**: After processing, the preview images are uploaded to a separate S3 bucket for further use.

---

## Requirements

- AWS Lambda environment with the `boto3` and `opencv-python` libraries.
- An S3 bucket containing the images and their corresponding YOLOv11 annotation files.
- A `data.yaml` file in YAML format, stored in S3, that contains the class names for the annotations.

### IAM Permissions

Ensure that the Lambda execution role has the following permissions:

- `s3:GetObject`: To fetch images and annotation files from the source S3 bucket.
- `s3:PutObject`: To upload preview images to the destination S3 bucket.

---

## Lambda Function Workflow

### 1. **Load Class Names from YAML File**
   - The function retrieves class names from a `data.yaml` file stored in S3. This file must have a list of class names under the `names` key.

### 2. **Identify and Process Latest Modified Images**
   - The function fetches the most recently modified images from the specified S3 bucket.
   - For each image, the corresponding annotation file (in `.txt` format) is retrieved from the same S3 bucket.
   - The annotations are parsed (in YOLO format) and used to draw bounding boxes on the image.

### 3. **Generate and Upload Preview Image**
   - The image is resized to 640x640 pixels.
   - Bounding boxes and class names are drawn on the image based on the annotations.
   - The processed preview image is then uploaded to a separate S3 bucket for preview purposes.

---

## Function Inputs

### 1. **S3 Bucket and Folder Paths**
   - `s3_bucket_name`: The source S3 bucket containing the images and annotations (e.g., `flipkartdataset1`).
   - `image_folder`: The folder in the S3 bucket where images are stored (e.g., `train/images`).
   - `labels_folder`: The folder containing annotation files for the images (e.g., `train/labels`).
   - `preview_bucket_name`: The S3 bucket where processed preview images will be uploaded (e.g., `flipkartprocessedpreview`).
   - `yaml_s3_uri`: The S3 URI for the `data.yaml` file (e.g., `s3://flipkartdataset1/data.yaml`).

### 2. **Number of Frames to Process**
   - `num_frames`: The number of latest images to process (for example, process the last 10 modified images).

---

## Code Explanation

### `load_class_names_from_s3(s3_bucket_name, yaml_s3_uri)`
   - This helper function loads class names from the `data.yaml` file stored in S3, which contains a list of class names for object detection.

### `lambda_handler(event, context)`
   - The main Lambda function that:
     - Loads class names from the `data.yaml` file.
     - Lists and identifies the most recently modified images in the specified S3 folder.
     - Fetches the corresponding annotation files and processes each image.
     - Draws bounding boxes and class names on the image.
     - Uploads the processed preview images to a separate S3 bucket.

---

## Example Event Structure

While the event passed to the Lambda function is not explicitly used in the current code, you can still include additional parameters. Here’s an example of the event structure:

```json
{
  "bucket_name": "flipkartdataset1",
  "image_folder": "train/images",
  "labels_folder": "train/labels",
  "preview_bucket_name": "flipkartprocessedpreview",
  "yaml_s3_uri": "s3://flipkartdataset1/data.yaml",
  "num_frames": 10
}
```

---

## Environment Variables

- `ACCESS_KEY`: Your AWS Access Key ID.
- `SECRET_KEY`: Your AWS Secret Access Key.
- `REGION_NAME`: The AWS region where your S3 buckets are located.

These should be configured in the Lambda environment or as part of the Lambda's IAM role.

---

## Sample Output

After the Lambda function completes processing, preview images will be uploaded to the specified preview S3 bucket. Example output:

```
Processing completed successfully for 10 images.
```

The preview images will be stored in the preview bucket with filenames such as:

```
previews/frame_name_preview.jpg
```

Where `frame_name` corresponds to the name of the image file being processed.

---

## Error Handling

If an error occurs during processing an image or annotation, the function will log the error and continue processing the remaining images. Example error log:

```
Error processing frame frame_name: <Error Message>
```

---

## Deployment

1. Package the Lambda function code and its dependencies (e.g., `boto3` and `opencv-python`) into a deployment package.
2. Upload the deployment package to AWS Lambda.
3. Set the necessary IAM permissions for the Lambda execution role to access the S3 buckets.
4. Trigger the Lambda function manually or set it to run on a schedule using CloudWatch Events.

---

## Conclusion

This Lambda function automates the creation of image previews by processing the latest modified images, adding bounding boxes based on YOLOv11 annotations, and storing the processed previews in another S3 bucket. This is useful for quick previewing and visualizing object detections in large datasets without needing to manually download and process each image.