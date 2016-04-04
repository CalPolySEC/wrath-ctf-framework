from ctf import create_app
import os
app = create_app()
app.run(debug=True, port=int(os.environ.get('PORT', '5000')))
