#! /bin/bash
cwd=`pwd`
if [ "$EUID" -ne 0 ]
	then echo "Please run as root"
	exit
fi

chmod +x *.sh

apt-get update
apt-get install libasound2-dev memcached python-pip mpg123 python-alsaaudio vlc
pip install -r requirements.txt

touch /var/log/alexa.log

echo "Enter your ProductID:"
read productid
echo ProductID = \"$productid\" >> creds.py

echo "Enter your Security Profile Description:"
read spd
echo Security_Profile_Description = \"$spd\" >> creds.py

echo "Enter your Security Profile ID:"
read spid
echo Security_Profile_ID = \"$spid\" >> creds.py

echo "Enter your Security Client ID:"
read cid
echo Client_ID = \"$cid\" >> creds.py

echo "Enter your Security Client Secret:"
read secret
echo Client_Secret = \"$secret\" >> creds.py

python ./auth_web.py 

echo "You can now reboot"