#!/bin/sh
set -e

if [ "$DJANGO_VERSION" ]
then
    pip install --force-reinstall Django==$DJANGO_VERSION
fi

if [ "$FLASK_VERSION" ]
then
    pip install --force-reinstall Flask==$FLASK_VERSION
fi
