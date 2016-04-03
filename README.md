# kompiler

Kompiler is a code compiler API server for compiling and executing code on an isolated docker container.

### Supported Environments

  - Python (2.7 or 3.5)
  - C++ (gcc 4.9)
  - C# (mono 4.2)
  - Javascript (node 5.9)

## Requirements

  - [Docker] (tested on Docker 1.10)
  - Python (for [Pyramid])
  - docker-py

## Setup

  1. Pull docker images
```sh
cat docker_images.txt | xargs -I images docker pull images
```
  2. Install python requirements
```sh
pip install -r requirements.txt
```

## Usage

  - Run the server
```sh
python kompiler.py
```
  - Try running
```sh
curl 'http://localhost:8000/compile/' -H 'content-type: application/json' --data-binary '{"code":"print(input())", "lang":"python", "stdin":"Hello World!"}'
```
  - Or use [Postman], though you may need to use urlencoded form data

#### Security considerations

> The code or scripts are run isolated on different containers and could not possibly affect the host (the way Docker works).
> These containers are created when calling the API and are removed permanently after getting the output or timing out.
> Networking is disabled by default.
> Still, there might be some vulnerabilities, please submit an issue regarding your concern/s.

## TODO

  - Move hard-coded settings outside the script (memory/CPU limitations, timeout, server settings)
  - Improve script transfer to container
  - Add other languages
  - Add some useful libraries for some environments

Feel free to submit pull requests

## Contributing

  1. Fork it!
  2. Create your feature branch: `git checkout -b my-new-feature`
  3. Commit your changes: `git commit -am 'Add some feature'`
  4. Push to the branch: `git push origin my-new-feature`
  5. Submit a pull request :)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

   [Pyramid]: <http://www.pylonsproject.org/>
   [Docker]: <https://www.docker.com/>
   [Postman]: <https://www.getpostman.com/>
