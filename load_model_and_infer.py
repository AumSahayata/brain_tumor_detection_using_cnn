import tensorflow as tf
import numpy as np
from tensorflow.keras.models import load_model

def preprocess_image(image_path):
    """
    Preprocess a single image for model inference.
    
    Args:
        image_path (str): Path to the image received from the frontend.
    
    Returns:
        tf.Tensor: Preprocessed image tensor ready for model prediction.
    """
    image = tf.io.read_file(image_path)
    image = tf.image.decode_png(image, channels=1)  # Ensure single-channel grayscale
    image = tf.image.resize(image, [224, 224])  # Resize to match model input
    image = tf.cast(image, tf.float32) / 255.0  # Normalize pixel values
    image = tf.expand_dims(image, axis=0)  # Add batch dimension
    
    return image

def predict(image_path, model_path="model/64-4.h5"):
    """
    Load the trained model and make a prediction on a single image.
    
    Args:
        image_path (str): Path to the input image.
        model_path (str): Path to the saved model file.
    
    Returns:
        int: Predicted class label.
        np.ndarray: Softmax probabilities for each class.
        float: Confidence score of the predicted class.
    """
    # Load the trained model
    model = load_model(model_path)
    
    # Preprocess the image
    image = preprocess_image(image_path)
    
    # Perform inference
    predictions = model.predict(image)
    predicted_class = np.argmax(predictions, axis=1)[0]  # Get class with highest probability
    confidence_score = np.max(predictions[0])  # Get the confidence score of the predicted class
    
    return predicted_class, predictions[0], confidence_score  # Return class label, probability distribution, and confidence score


print(predict('Dataset/Testing/pituitary/Te-pi_0012.jpg'))