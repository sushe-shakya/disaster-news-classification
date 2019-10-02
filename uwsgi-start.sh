uwsgi --socket 0.0.0.0:5000 --protocol=http --workers $(nproc) --threads 2 --enable-threads -w wsgi
