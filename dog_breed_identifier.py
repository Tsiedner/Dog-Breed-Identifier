# -*- coding: utf-8 -*-
"""Dog Breed Identifier

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Kw8hdUrELe9JmKv7uNL3kSOH1e6U6Bv8

### 🐶 End-to-end Multi-class Dog Breed Classification

This notebook builds an end-to-end multi-class image classifier
using TensorFlow 2.0 and TensorFlow Hub.

## 1. Problem

Identifying the breed of a dog given an image of a dog.

## 2. Data

The data is from Kaggle's dog breed identification competition.
https://www.kaggle.com/c/dog-breed-identification/data

## 3. Evaluation

A file with prediction probabilities for each dog breed of each test image. 
https://www.kaggle.com/c/dog-breed-identification/overview/evaluation

## 4. Features

Info about the data:
* We're dealing with images (unstructured data) so we'll use deep learning/ transfer learning.
* There are 120 breeds of dogs (this means there are 120 different classes).
* There are around 10,000+ images in the training set.(these images are labeled)
* There are around 10,000+ images in the test set (these images are not labeled)
"""

# Unzip th uploaded data in Google Drive
#!unzip "/content/drive/MyDrive/Dog Breed Identifier/dog-breed-identification.zip" -d "drive/MyDrive/Dog Breed Identifier/"

"""## Get our workspace ready

* Import TenserFlow 2.7
* Import TensorFlow Hub
* Make sure we're using a GPU
"""

# import necessary tools into Colab
import tensorflow as tf
import tensorflow_hub as hub
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
print("TF version", tf.__version__)
print("TF Hub Version", hub.__version__)

# check for GPU availability
print("GPU", "available :^)" if tf.config.list_physical_devices("GPU") else "not available :^(")

"""## Getting our data ready (turning it into Tesors)

The data has to be in numerical format by turning it into Tensors
"""

# Access data and check out the labels
labels_csv= pd.read_csv("/content/drive/MyDrive/Dog Breed Identifier/labels.csv")
print(labels_csv.describe())
labels_csv.head()

# Check images per breed
labels_csv["breed"].value_counts().plot.bar(figsize=(20, 10));

labels_csv["breed"].value_counts().median()

# check an image
from IPython.display import Image
Image("drive/MyDrive/Dog Breed Identifier/train/000bec180eb18c7604dcecc8fe0dba07.jpg")

"""### Getting images and their labels

Get a list of the images and their pathnames

"""

# create pathnames from image ID's
filenames = ["drive/MyDrive/Dog Breed Identifier/train/" + fname + ".jpg" for fname in labels_csv["id"]]

# checking first 10
filenames[:10]

# look at if the number file names is equal to the number of image files
import os
if len(os.listdir("drive/MyDrive/Dog Breed Identifier/train/")) == len(filenames):
  print("Filenames match the amount of files")
else:
  print("File names do not match the amount of files")

# double checking
Image(filenames[422])

labels_csv["breed"][422]

"""Now that the training filepaths are in a list, now I'll prepare the labels"""

# turn labels into numpy array
labels = labels_csv["breed"]
labels = np.array(labels)
labels

len(labels)

# check for missing data
if len(labels) == len(filenames):
  print("Number of labels and filenames match")
else:
  print("Numbers don't match")

# Find the number of unique labels
unique_breeds = np.unique(labels)
len(unique_breeds)

# turn every label into a boolean array
boolean_labels = [label == unique_breeds for label in labels]
boolean_labels[:2]

# checking
len(boolean_labels)

# Turning boolean array into integers
print(labels[0]) # original label
print(np.where(unique_breeds == labels[0])) # index where label occurs
print(boolean_labels[0].argmax()) # index where label occurs in boolean array
print(boolean_labels[0].astype(int)) # there will be a 1 where the same label occurs

"""### Creating a validation set"""

# setup X and y variables
X = filenames
y = boolean_labels

"""Start off with 1000 ish images and increase it as needed"""

# set number of image to use for experimenting
NUM_IMAGES = 1000 #@param {type:"slider", min:1000, max:10000, step:1000}

# split data into train and validation sets
from sklearn.model_selection import train_test_split

# split them into training and validation of total size NUM_IMAGES
X_train, X_val, y_train, y_val = train_test_split(X[:NUM_IMAGES],
                                                  y[:NUM_IMAGES],
                                                  test_size=0.2,
                                                  random_state=42)
len(X_train), len(y_train), len(X_val), len(y_val)

# check training data
X_train[:2], y_train[:2]

"""## Preprocessing Images: turning images into Tensors

Write a function that:
1. Take an image filepath as input
2. Use Tenserflow to read the fila and save it to a variable `image`
3. Turn our `image` into Tensors
4. Normalize `image`
5. Resize the `image` to bea shape (224, 224)
6. Return the modified `image`
"""

# define image size
IMG_SIZE = 224

# creat a function for preprocessing images
def process_image(image_path):
  """
  Takes an image file path an turns it into a tensor.
  """
  # read in an image file
  image = tf.io.read_file(image_path)

  # turn the image inot tensor with 3 color channels
  image = tf.image.decode_jpeg(image, channels=3)

  # convert the color channel values from 0-255 to 0-1 values 
  image = tf.image.convert_image_dtype(image, tf.float32)

  # Resize the image to (224, 224)
  image = tf.image.resize(image, size=[IMG_SIZE, IMG_SIZE])

  return image

"""## Turning the data into batches

Turn the images into batches because a GPU has a limited number of memory. That's why I'll do a 32 image batch size (if needed I'll adjust that)

The data needs to be in Tensor tuples:
`(image, label)`
"""

# function that returns a tuple of tensors
def get_image_label(image_path, label):
  """
  Takes image path name and the associated label, processes the image and returns a tuple of (image, label)
  """
  image = process_image(image_path)
  return image, label

# demo of the above
(process_image(X[422]), tf.constant(y[422]))

"""Make a function that turns `X` and `y` into batches."""

# defin the batch size, 32 is where I'll start
BATCH_SIZE = 32

# function to turn data into batches
def create_data_batches(X, y=None, batch_size=BATCH_SIZE, valid_data=False, test_data=False):
  """
  Creates batches of data out of image (X) and label (y) pairs.
  SHuffles the data if it's training data but doesn't shuffle if it's validation data.
  Also accepts test data as input (no labels).
  """
  # if test dataset, there are no labels
  if test_data:
    print("Creating test data batches")
    data = tf.data.Dataset.from_tensor_slices((tf.constant(X)))
    data_batch = data.map(process_image).batch(BATCH_SIZE)
    return data_batch

  # If valid data set, don't shuffle it
  elif valid_data:
    print("Creating validation data batches")
    data = tf.data.Dataset.from_tensor_slices((tf.constant(X), 
                                               tf.constant(y)))
    data_batch = data.map(get_image_label).batch(BATCH_SIZE)
    return data_batch
  # if training data set, shuffle
  else:
    print("Create training data batches")
    data = tf.data.Dataset.from_tensor_slices((tf.constant(X),
                                               tf.constant(y)))
    # shuffle pathnames and labels before mapping because it's shorter that way
    data = data.shuffle(buffer_size=len(X))

    # create (X, y) tuples and turns the image path into preprossed image
    data = data.map(get_image_label)

    # turn trining data into batches
    data_batch = data.batch(BATCH_SIZE)
    return data_batch

# create training and validation data batches
train_data = create_data_batches(X_train, y_train)
val_data = create_data_batches(X_val, y_val, valid_data=True)

# check the different attributes
train_data.element_spec, val_data.element_spec

"""### Visualizing Data Batches"""

# function for viewing images in data batch
def show_25_images(images, labels):
  """
  Displays a plot of 25 images and their labels from a data batch
  """
  # setup figure
  plt.figure(figsize=(10, 10))
  # loop through 25
  for i in range(25):
    # create subplots
    ax = plt.subplot(5, 5, i+1)
    # display image
    plt.imshow(images[i])
    # add the image label as the title
    plt.title(unique_breeds[labels[i].argmax()])
    # turn the grid lines off
    plt.axis("off")

train_images, train_labels = next(train_data.as_numpy_iterator())
len(train_images), len(train_labels)

# Use visualiztion  function
show_25_images(train_images, train_labels)

# visualize val set
val_images, val_labels = next(val_data.as_numpy_iterator())
show_25_images(val_images, val_labels)

"""## Building the model

Things that are defined:
1. The input shape
2. The output shape
3. The URL of the model we want to use.

"""

# setup intput shape to the model
INPUT_SHAPE = [None, IMG_SIZE, IMG_SIZE, 3]

# setup output shape
OUTPUT_SHAPE = len(unique_breeds)

# setup model URL from TenserFlor Hub
MODEL_URL = "https://tfhub.dev/google/imagenet/mobilenet_v2_130_224/classification/5"

"""Put inputs and outputs together in a Keras DL model.

Create a function that:

* Takes the input, output shape and model
* Defines the layers in the Keras model in a sequential fashion
* Compiles the model (tells how it should be evaluated and improved)
* Build the model (tells the model the input shape)
* Returns the model

Steps are from here: https://www.tensorflow.org/guide/keras/sequential_model



"""

# function that creates a Keras model
def create_model(input_shape=INPUT_SHAPE, output_shape=OUTPUT_SHAPE, model_url=MODEL_URL):
  print("Building model with:", MODEL_URL)
  """
  Create a function that builds a Keras model in sequential fashion, compiles the model and builds the model. 
  """

  #Setup the model layers
  model = tf.keras.Sequential([
    hub.KerasLayer(MODEL_URL), # layer 1 (input layer)
    tf.keras.layers.Dense(units=OUTPUT_SHAPE,
                          activation="softmax") # layer 2 (output layer)
  ])

  # Compile the model
  model.compile(
      loss=tf.keras.losses.CategoricalCrossentropy(),
      optimizer=tf.keras.optimizers.Adam(),
      metrics=["accuracy"]
  )

  # Build the model
  model.build(INPUT_SHAPE)

  return model

model = create_model()
model.summary()

"""## Create callbacks

Callback can be used during training to check or save its progress, or to stopr training early if the model stops improving

Create two callbacks:
1. TensorBoard to help track our models progress
2. Another for early stopping to prevent our model from training for too long 

### TensorBoard Callback

Three things to setup TensorBoard callback:
1. Load tensorboard notebook extension.
2. Create a tensorboard callback that can save logs to a directory and then pass it to the models `fit()` function.
3. Visualize the models training logs with the `%tensorboard` magic function.(after model training)
"""

# Commented out IPython magic to ensure Python compatibility.
# Load TensorBoard notebook
# %load_ext tensorboard

import datetime

# create a function to build a tensorboard callback
def create_tensorboard_callback():
  # create a log directory for storing tensorboard logs
  logdir = os.path.join("drive/MyDrive/Dog Breed Identifier/logs",
                        datetime.datetime.now().strftime("%Y%m%d%-%H%M%S")) # logs get tracked when experiments run

  return tf.keras.callbacks.TensorBoard(logdir)

"""### Early Stopping Callback

Stops overfitting by stopping training if a certain evaluation metric stops improving.

https://www.tensorflow.org/api_docs/python/tf/keras/callbacks/EarlyStopping
"""

# early stopping callback
early_stopping = tf.keras.callbacks.EarlyStopping(monitor="val_accuracy",
                                                  patience=3)

"""## Training a model on a subset of data

First model will be trained on 1000 images to make sure I didn't mess up 😅 
"""

NUM_EPOCHS = 100 #@param {type:"slider", min:10, max:100, step:10}

# check that the GPU is still connected
print("GPU", "available :^)"if tf.config.list_physical_devices("GPU") else "not available :^(")

"""Create a function that trains a model

* Create a model using `create_model()`
* Setup a TensorBoard using `create_tensorboard_callback()`
* Call the `fit()` function on our model passing it the training data, validation data, number of epochs to train for `(NUM_EPOCHS)` and the callbacks we'd like to use
* Return the model


"""

# Function to train a model and return a trained model
def train_model():
  """
  Trains a given model and returns the trained version.
  """
  # create model
  model = create_model()

  # create ne TensorBoard session everytim a model is trained
  tensorboard = create_tensorboard_callback()

  # fit model to data passing it the callbacks
  model.fit(x=train_data,
            epochs=NUM_EPOCHS,
            validation_data=val_data,
            validation_freq=1,
            callbacks=[tensorboard, early_stopping])
  # return fitted model
  return model

# fit the model to the data
model = train_model()

"""### Checking the TensorBoard logs

TensorBoard magic function (`%tensorboard`) will access log directory that was created up top and visualize its contents.
"""

# Commented out IPython magic to ensure Python compatibility.
# %tensorboard --logdir drive/MyDrive/Dog\ Breed\ Identifier/logs

"""### Making and evaluating prediction using the trained model"""

# predictions on the validation data (not used to train on)
predictions = model.predict(val_data, verbose=1)
predictions

predictions.shape

# First prediction
index = 42
print(predictions[index])
print(f"Max value (probability of prediction): {np.max(predictions[index])}")
print(f"Sum: {np.sum(predictions[index])}")
print(f"Max index: {np.argmax(predictions[index])}")
print(f"Predicted label: {unique_breeds[np.argmax(predictions[index])]}")

# Turn prediction probabilities in their labels
def get_pred_label(prediction_probabilities):
  """
  Turns an array of predictions into a label.
  """
  return unique_breeds[np.argmax(prediction_probabilities)]

# get a predicted labe based on prediction probabilities
pred_label = get_pred_label(predictions[99])
pred_label

"""### Unbatchifying the dataset"""

# function for unbatchifying
def unbatchify(data):
  """
  Turns batched dataset of (image, label) Tensors, into separate arrays of images and labels.
  """
  images = []
  labels = []
  # loup through unbatched data
  for image, label in val_data.unbatch().as_numpy_iterator():
    images.append(image)
    labels.append(unique_breeds[np.argmax(label)])
  return images, labels

# Unbatchifing the validation data
val_images, val_labels = unbatchify(val_data)
val_images[0], val_labels[0]

"""Make functions to visualize: 
* Prediction labels
* Validation labels
* Validation images

Create a function that:
* Takes an array of prediction probabilities, an array of truth labels and an array of images and an integer.
* Converts the prediction probabilities to a prediction label.
* Plots the predicted label, its predicted probability, truth label and the targeted image in one plot.
"""

def plot_pred(prediction_probabilities, labels, images, n=1):
  """
  View the prediction, ground truth and image for sample n
  """
  pred_prob, true_label, image = prediction_probabilities[n], labels[n], images[n]

  # Get the pred label
  pred_label = get_pred_label(pred_prob)

  # Plot image and remove ticks
  plt.imshow(image)
  plt.xticks([])
  plt.yticks([])

  # Make the color of the title green for right and red for wrong
  if pred_label == true_label:
    color = "green"
  else:
    color = "red"

  # Plot title to predicted, probability of prediction and truth label
  plt.title("{} {:2.0f}% {}".format(pred_label,
                                    np.max(pred_prob)*100,
                                    true_label),
                                    color=color)

plot_pred(prediction_probabilities = predictions,
          labels = val_labels,
          images = val_images, 
          n=70)

"""## Function to view top 10 predictions

Function will:
* Take an input of prediction probabilities array and a ground truth array and an integer
* Find the prediction using `get_pred_label()`
* Find the top 10:
  * Prediction probabilities indexes
  * Prediction probabilities values
  * Prediction labels
* Plot the top 10 probability values and labels, coloring true labels green
"""

def plot_pred_conf(prediction_probabilities, labels, n=1):
  """
  Plots the top 10 highest prediction confidences along with the truth label for sample n.
  """
  pred_prob, true_label = prediction_probabilities[n], labels[n]

  # Get the prediction label
  pred_label = get_pred_label(pred_prob)

  # Top 10 predicition confidence indexes
  top_10_pred_indexes = pred_prob.argsort()[-10:][::-1]

  # Top 10 prediction confidence values
  top_10_pred_values = pred_prob[top_10_pred_indexes]

  # Top 10 prediction labels
  top_10_pred_labels = unique_breeds[top_10_pred_indexes]

  # Setup plot
  top_plot = plt.bar(np.arange(len(top_10_pred_labels)),
                     top_10_pred_values,
                     color="grey")
  plt.xticks(np.arange(len(top_10_pred_labels)),
             labels=top_10_pred_labels,
             rotation="vertical")
  
  # Change color of true label
  if np.isin(true_label, top_10_pred_labels):
    top_plot[np.argmax(top_10_pred_labels == true_label)].set_color("green")
  else:
    pass

plot_pred_conf(prediction_probabilities=predictions,
               labels=val_labels,
               n=9)

# FUnction for checking out a few predictions and their different values
def plot_pred_dif(prediction_probabilities, labels, n=1):
  """
  Checks out a few predcions and their values.
  """
  i_multiplier = 20
  num_rows = 3
  num_cols = 2
  num_images = num_rows*num_cols
  plt.figure(figsize=(10*num_cols, 5*num_rows))
  for i in range(num_images):
    plt.subplot(num_rows, 2*num_cols, 2*i+1)
    plot_pred(prediction_probabilities=predictions,
            labels=val_labels,
            images=val_images,
            n=i+i_multiplier)
    plt.subplot(num_rows, 2*num_cols, 2*i+2)
    plot_pred_conf(prediction_probabilities=predictions,
                 labels=val_labels,
                 n=i+i_multiplier)
  plt.tight_layout(h_pad=1.0)

plot_pred_dif(prediction_probabilities=predictions,
              labels=val_labels)

"""## Saving and reloading the model


"""

# Function to save model
def save_model(model, suffix=None):
  """
  Saves the model in the models directory and appends a suffix.
  """
  # Create a model directory pathname with timestamp
  modeldir = os.path.join("drive/MyDrive/Dog Breed Identifier/Models",
                          datetime.datetime.now().strftime("%Y%m%d-%H%M%s"))
  # save format
  model_path = modeldir + "-" + suffix + ".h5"
  print(f"Saving model to: {model_path}...")
  model.save(model_path)
  return model_path

# Function to load model
def load_model(model_path):
  """
  Loads a saved model from a specified path.
  """
  print(f"Loading saved model from: {model_path}")
  model = tf.keras.models.load_model(model_path,
                                     custom_objects={"KerasLayer":hub.KerasLayer})
  return model

# check if save works 
save_model(model, suffix="1000-images-mobilenetv2-Adam")

# check if load works
loaded_1000_image_model = load_model("drive/MyDrive/Dog Breed Identifier/Models/20220117-15191642432790-1000-images-mobilenetv2-Adam.h5")

# check pre-saved model
model.evaluate(val_data)

# check saved model data
loaded_1000_image_model.evaluate(val_data)

"""## Training model on the full data"""

# Creat a data batch with full data set
full_data = create_data_batches(X, y)

# Checking
full_data

# Create a model for full model
full_model = create_model()

# create full model callbacks
full_model_tensorboard = create_tensorboard_callback()
# To prevent overfitting
full_model_early_stopping = tf.keras.callbacks.EarlyStopping(monitor="accuracy",
                                                             patience=3)

"""**NOTE:** The cell below will take a little bit (like 30ish minutes) because the GPU has to load all of the images into memory."""

# Fit the full model to full data
full_model.fit(x=full_data,
               epochs=NUM_EPOCHS,
               callbacks=[full_model_tensorboard, full_model_early_stopping])

#save_model(full_model, suffix="full-image-set-mobilenetv2-Adam")

# load in full model
loaded_full_model = load_model("drive/MyDrive/Dog Breed Identifier/Models/20220117-16091642435743-full-image-set-mobilenetv2-Adam.h5")

"""## Making predictions on the test data set

Turn test data into Tensor batches using `create_data_batches()`

To make predictions:
* Get test image filenames
* Convert using `create_data_batches()`
* Set thee `test_data` parameter to `True`
* Make a predictions array by passing the test batches to the `predict()` method called on the model
"""

# Load test image filenames
test_path = "drive/MyDrive/Dog Breed Identifier/test/"
test_filenames = [test_path + fname for fname in os.listdir(test_path)]
test_filenames[:10]

# Create test data batch
test_data = create_data_batches(test_filenames, test_data=True)

"""**NOTE** The next cell will take like maybe an hour to run 😅"""

# Prediction array 
#test_predictions = loaded_full_model.predict(test_data,
                                             verbose=1)

# Save predictions to csv file
#np.savetxt("drive/MyDrive/Dog Breed Identifier/preds_array.csv", test_predictions, delimiter=",")

# Load predictions from csv
test_predictions = np.loadtxt("drive/MyDrive/Dog Breed Identifier/preds_array.csv", delimiter=",")

test_predictions[:10]

test_predictions.shape

"""## Preparing test data set predictions for Kaggle

* Create pandas DataFrame with ID column and column for each dog breed
* Add data to the ID column by extracting the test image ID's from their filepaths
* Add the prediction probabilities to each of the dog breed columns
* Export the DataFrame as a CSV
"""

# create a pandas dataframe
#preds_df = pd.DataFrame(columns=["id"] + list(unique_breeds))
#preds_df.head()

# appending test image ID's to preds_df
#test_ids = [os.path.splitext(path)[0] for path in os.listdir(test_path)]
#preds_df["id"] = test_ids

preds_df.head()

# Add prediction probabilities to each dog breed column
#preds_df[list(unique_breeds)] = test_predictions
#preds_df.head()

# save pred_df to csv
#preds_df.to_csv("drive/MyDrive/Dog Breed Identifier/full_model_preds_submission_1_mobilenetV2.csv",
                index=False)

"""## Predictions on my dogs!

What to do:
* Get the filepaths
* Turn them into data batches using `create_data_batches` and set `test_data` parameter to `True`
* Pass the custom image data batch to our model's `predict()`
* Convert the prediction outpur probabilities to prediction labels
* Compare the predicted label to the custom images

"""

# setup the custom path
custom_path = "drive/MyDrive/Dog Breed Identifier/MyDogs/"
custom_image_paths = [custom_path + fname for fname in os.listdir(custom_path)]

custom_image_paths

# turn images into batches
custom_data = create_data_batches(custom_image_paths, test_data=True)
custom_data

# Make predictions
custom_preds = loaded_full_model.predict(custom_data)
custom_preds.shape

# Get labels
custom_pred_labels = [get_pred_label(custom_preds[i]) for i in range(len(custom_preds))]
custom_pred_labels

# get custom images
custom_images = []
# loop through unbatched data
for image in custom_data.unbatch().as_numpy_iterator():
  custom_images.append(image)

# Check custom image predictions
plt.figure(figsize=(10, 10))
for i, image in enumerate(custom_images):
  plt.subplot(1, 4, i+1)
  plt.xticks([])
  plt.yticks([])
  plt.title(custom_pred_labels[i])
  plt.imshow(image)

