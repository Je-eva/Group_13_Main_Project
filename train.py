import os
import cv2
import numpy as np
from keras.layers import Conv3D, ConvLSTM2D, Conv3DTranspose, Input
from keras.models import Sequential
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.preprocessing.image import img_to_array, load_img

# Set the environment variable to disable oneDNN optimizations
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

def process_video(video_path, train_images_path, fps=5):
    cap = cv2.VideoCapture(video_path)
    count = 0
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return

    success = True
    while True:
        success, frame = cap.read()
        if not success:
            break
        if count % fps == 0:
            frame_path = os.path.join(train_images_path, f"{count:03d}.jpg")
            cv2.imwrite(frame_path, frame)
            print(f"Saved frame {count} to {frame_path}")
        count += 1
    cap.release()
    print(f"Processed video: {video_path}, total frames: {count}")


store_image = []
train_path = 'normal'
fps = 5
train_videos = os.listdir(train_path)
train_images_path = os.path.join(train_path, 'frames')
os.makedirs(train_images_path, exist_ok=True)

for video in train_videos:
    video_path = os.path.join(train_path, video)
    process_video(video_path, train_images_path, fps=fps)
    images = os.listdir(train_images_path)
    print(f"Processing video: {video}, number of frames: {len(images)}")
    for image in images:
        image_path = os.path.join(train_images_path, image)
        image = load_img(image_path)
        image = img_to_array(image)
        image = cv2.resize(image, (227, 227), interpolation=cv2.INTER_AREA)
        gray = 0.2989 * image[:, :, 0] + 0.5870 * image[:, :, 1] + 0.1140 * image[:, :, 2]
        store_image.append(gray)

if len(store_image) > 0:
    print("Total images stored:", len(store_image))

    store_image = np.array(store_image)
    a, b, c = store_image.shape
    store_image.resize(b, c, a)
    store_image = (store_image - store_image.mean()) / (store_image.std())
    store_image = np.clip(store_image, 0, 1)
    np.save('training.npy', store_image)
    print("training.npy saved successfully.")
else:
    print("No images stored, check if the video files are processed correctly.")

# Define stae_model
from keras.callbacks import ModelCheckpoint, EarlyStopping

# Set the environment variable to disable oneDNN optimizations
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Define the model checkpoint callback
callback_save = ModelCheckpoint("saved_model.keras", monitor="loss", save_best_only=True)

# Define early stopping callback
callback_early_stopping = EarlyStopping(monitor='loss', patience=3)

# Define the model architecture
stae_model = Sequential()
stae_model.add(Input(shape=(227, 227, 10, 1)))  # Use Input layer for specifying input shape

stae_model.add(Conv3D(filters=128, kernel_size=(11, 11, 1), strides=(4, 4, 1), padding='valid', activation='tanh'))
stae_model.add(Conv3D(filters=64, kernel_size=(5, 5, 1), strides=(2, 2, 1), padding='valid', activation='tanh'))
stae_model.add(ConvLSTM2D(filters=64, kernel_size=(3, 3), strides=1, padding='same', dropout=0.4, recurrent_dropout=0.3, return_sequences=True))
stae_model.add(ConvLSTM2D(filters=32, kernel_size=(3, 3), strides=1, padding='same', dropout=0.3, return_sequences=True))
stae_model.add(ConvLSTM2D(filters=64, kernel_size=(3, 3), strides=1, return_sequences=True, padding='same', dropout=0.5))
stae_model.add(Conv3DTranspose(filters=128, kernel_size=(5, 5, 1), strides=(2, 2, 1), padding='valid', activation='tanh'))
stae_model.add(Conv3DTranspose(filters=1, kernel_size=(11, 11, 1), strides=(4, 4, 1), padding='valid', activation='tanh'))

stae_model.compile(optimizer='adam', loss='mean_squared_error', metrics=['accuracy'])

# Load training data
training_data = np.load('training.npy')
frames = training_data.shape[2]
frames = frames - frames % 10

training_data = training_data[:, :, :frames]
training_data = training_data.reshape(-1, 227, 227, 10)
training_data = np.expand_dims(training_data, axis=4)
target_data = training_data.copy()

# Training parameters
epochs = 5
batch_size = 1

# Train the model
stae_model.fit(training_data, target_data,
               batch_size=batch_size,
               epochs=epochs,
               callbacks=[callback_save, callback_early_stopping]
               )

# Save the model
stae_model.save("saved_model.keras")
np.save('training.npy', store_image)