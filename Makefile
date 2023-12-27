install-gstreamer:
	sudo apt update && sudo apt upgrade
	sudo apt-get install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
		libgstreamer-plugins-bad1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
		gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-tools \
		gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl gstreamer1.0-gtk3 gstreamer1.0-qt5 gstreamer1.0-pulseaudio
	sudo apt install libcairo2-dev libxt-dev libgirepository1.0-dev
	pip3 install pycairo PyGObject