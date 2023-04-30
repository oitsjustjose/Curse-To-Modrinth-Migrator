FROM python:3.10-buster

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y libasound2 \
    libnspr4 \
    libnss3 \
    libxss1 \
    xdg-utils \
    unzip \
    libappindicator1 \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libgbm1 \
    libgtk-3-0 \
    libu2f-udev \
    libvulkan1 \
    libxkbcommon0 \
    xvfb 
RUN apt-get -f install

# # Install Google Chrome
RUN wget http://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome*.deb && rm google-chrome*.deb

# Patch to make XVFB actually work
RUN mkdir /tmp/.X11-unix
RUN chmod 1777 /tmp/.X11-unix
RUN chown root /tmp/.X11-unix/

COPY . .

RUN pip install -r requirements.txt

CMD ["python", "src/__main__.py"]