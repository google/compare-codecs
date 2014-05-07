#!/usr/bin/python
#
# The MPEG CFP rates, linked to filenames.
rates={}
# MPEG Royalty-Free Codec CFP, early 2013
# TODO(hta): Encapsulate rates and files into an object.
# Once that is done, we can make an object with these rates.
#rates["A"] = (2500, 3500, 5000, 8000, 14000)
#rates["B1"] = (1000, 1600, 2500, 4000, 6000)
#rates["B2"] = (2000, 3000, 4500, 7000, 10000)
#rates["C"] = (384, 512, 768, 1200, 2000)
#rates["D"] = (256, 384, 512, 850, 1500)
#rates["E"] = (256, 384, 512, 850, 1500)

files={}
#files["A"] = ("Traffic_2560x1600_30_crop.yuv",
#"PeopleOnStreet_2560x1600_30_crop.yuv")
#files["B1"] = ("Kimono1_1920x1080_24.yuv",
#"ParkScene_1920x1080_24.yuv")
# B2 files are missing: cactus and basketball drive
#files["B2"] = ()
#files["C"] = ("BasketballDrill_832x480_50.yuv",
#"BQMall_832x480_60.yuv",
#"PartyScene_832x480_50.yuv",
#"RaceHorses_832x480_30.yuv")

# Missing file BQSquare
#files["D"] = ("BasketballPass_416x240_50.yuv",
#"BlowingBubbles_416x240_50.yuv",
#"RaceHorses_416x240_30.yuv")


#files["E"] = ("FourPeople_1280x720_60.yuv",
#"Johnny_1280x720_60.yuv",
#"KristenAndSara_1280x720_60.yuv")

# MPEG codec comparision test, December 2013
rates = {}
rates['A'] = (1600, 2500, 4000, 6000)
rates['B'] = (3000, 4500, 7000, 10000)
rates['C'] = (512, 768, 1200, 2000)
rates['D'] = (384, 512, 850, 1500)

files['A'] = ("Kimono1_1920x1080_24.yuv",
"ParkScene_1920x1080_24.yuv")
files['B'] = ("Cactus_1920x1080_50.yuv",
"BasketballDrive_1920x1080_50.yuv")
files['C'] = ("BasketballDrill_832x480_50.yuv",
"BQMall_832x480_60.yuv",
"PartyScene_832x480_50.yuv",
"RaceHorses_832x480_30.yuv")

files["D"] = ("FourPeople_1280x720_60.yuv",
"Johnny_1280x720_60.yuv",
"KristenAndSara_1280x720_60.yuv")


def TweakAll():
  for classname in files.keys():
    for file in files[classname]:
      for rate in rates[classname]:
        print "./vp8tweaker --codec=vp8_mpeg_1d --loop ", rate, \
               "../mpeg_video/" + file + '&'


if __name__ == '__main__':
  TweakAll()
