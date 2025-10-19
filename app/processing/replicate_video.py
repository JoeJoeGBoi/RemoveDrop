import os
import replicate
from ..utils.logger import get_logger

log = get_logger(__name__)

# Initialize client once
replicate_client = replicate.Client(api_token=os.environ["REPLICATE_API_TOKEN"])

def process_video(input_path: str) -> dict:
    """
    Sends the video to Replicate Robust Video Matting and returns output URL.
    Returns:
      { "output_url": str, "meta": dict }
    """
    # Model reference can change; using a popular RVM implementation
    # You can swap to a pinned version if you prefer stability.
    model_ref = "pfnet/robust-video-matting"
    log.info("Submitting video to Replicate model: %s", model_ref)

    with open(input_path, "rb") as f:
        # Many RVM endpoints accept file uploads under key 'video' or 'input_video'
        # The official replicate SDK normalizes this via input param mapping.
        prediction = replicate_client.run(
            f"{model_ref}",
            input={
                "video": f,            # replicate handles file upload
                "backbone": "resnet50",
                "downsample_ratio": 0.25,   # tradeoff speed/quality
                "output_format": "video",
            },
        )

    # The SDK returns a URL or list of URLs depending on the model.
    if isinstance(prediction, list):
        output_url = prediction[0]
    elif isinstance(prediction, str):
        output_url = prediction
    elif isinstance(prediction, dict) and "output" in prediction:
        output_url = prediction["output"]
    else:
        raise RuntimeError(f"Unexpected Replicate response: {prediction!r}")

    log.info("Replicate processing complete: %s", output_url)
    return {"output_url": output_url, "meta": {"model": model_ref}}
