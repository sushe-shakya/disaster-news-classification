uwsgi --socket 0.0.0.0:5001 --protocol=http --workers $(nproc) --threads 2 --enable-threads -w wsgi
