from ctf import create_app
import os
app = create_app()
app.run(debug=True,
        host=os.environ.get('HOST', '127.0.0.1'),
        port=int(os.environ.get('PORT', '5000')))
