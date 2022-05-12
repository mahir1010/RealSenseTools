#Usage extract_nth_frames.sh <root> <video> <n> <seek>
root=${1%/}
name=$(basename -- "$2")
name="${name%.*}"
echo $name
mkdir "$root/$name"
if [ "$#" -gt 3 ]; then
        ffmpeg -i $2 -ss $4 -vf "select=not(mod(n\,$3))" -vsync vfr "$root/$name/img_%03d.png"
else
        ffmpeg -i $2 -vf "select=not(mod(n\,$3))" -vsync vfr "$root/$name/img_%03d.png"
fi


