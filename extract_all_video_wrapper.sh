# Usage extract_nth_frames.sh <root> <n> <seek>
root=${1%/}
for vid in "$root"/*.mp4
do
    ./extract_nth_frames.sh $root $vid $2 $3
done
