#! /bin/bash

a=1
mkdir "sequence"
for i in *.jpg; do
  new=$(printf "%04d.jpg" "$a") #04 pad to length of 4
  mv -i -- "$i" "sequence/$new"
  let a=a+1
done

