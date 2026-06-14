#!/usr/bin/sh

rsync -av kb/docs data/raw
rsync -av kb/templates data/raw
rsync -av kb/samples data/raw
