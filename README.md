# Audiovisualizer

An interactive 3D audiovisualizer built with Three.js that reacts to audio data to create dynamic visual effects. The project uses a sphere geometry that moves in a wave-like pattern based on audio input and rotates continuously.

## Features

- **3D Visualization**: Utilizes Three.js to render a rotating sphere in wireframe style.
- **Audio Integration**: Responds to audio data and adjusts the geometry accordingly.
- **Interactivity**: Allows users to rotate and zoom the view with OrbitControls.

## Installation

1. **Clone the repository**:
   ```bash
   git clone git@github.com:weird-trust/audiovisualizer.git
   cd audiovisualizer
Install dependencies:
Ensure Node.js and npm are installed, then run:
bash



npm install
Start the project:
bash



npm run dev

Usage
Play Audio: The project is configured to play a local audio file. Ensure the file is present at the specified path.
Adjust View: Use mouse or touch gestures to rotate and zoom the view.
Customization
Change Audio Source: You can change the audio source by modifying the path in the src attribute of the Audio element in the code.
Modify Geometry: Experiment with different geometries and material properties to achieve various visual effects.
License
This project is licensed under the MIT License. See the LICENSE file for more details.
