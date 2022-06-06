<div id="top"></div>

<!-- PROJECT SHIELDS -->

[<div align="center"> ![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![MIT License][license-shield]][license-url]
[![Issues][issues-shield]][issues-url]
[![Issues Closed][issues-closed-shield]</div>][issues-closed-url]

<br />

<!-- PROJECT LOGO -->

![voice-presentation-control](https://socialify.git.ci/wst24365888/voice-presentation-control/image?description=1&font=KoHo&name=1&owner=1&pattern=Circuit%20Board&theme=Light)

<br />
<div align="center">
<p align="center">
    <a href="https://github.com/wst24365888/voice-presentation-control#usages"><strong>Explore Usages »</strong></a>
    <br />
    <br />
    <a href="https://github.com/wst24365888/voice-presentation-control/issues">Report Bug</a>
    ·
    <a href="https://github.com/wst24365888/voice-presentation-control/issues">Request Feature</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#try-it">Try It</a></li>
      </ul>
    </li>
    <li><a href="#actions">Actions</a></li>
    <li><a href="#usages">Usages</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->

## About The Project

`voice-presentation-control` is a tool that allows you to control your presentation using voice when you don't have a presentation pen or when it's inconvinient to use the keyboard.

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- GETTING STARTED -->

## Getting Started

### Installation

#### Using `pip`

`pip install voice-presentation-control`

#### Using `.whl`

See [releases](https://github.com/wst24365888/voice-presentation-control/releases).

> :warning: **If you encounter an error while installing** `PyAudio` (which is in our dependencies):
>   - For Windows users, visit [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) to pick appropriate `.whl` to install.
>   - For OS X users, run `brew install portaudio`, then `pip install pyaudio`.
>   - For Debian-derived Linux distributions (like Ubuntu and Mint) users, run `sudo apt-get install libasound-dev libportaudio2 libportaudiocpp0 portaudio19-dev && pip install pyaudio`.

### Try It

Just open your terminal, simply type `vpc start` and boom, it works!

## Actions

To check the default configuration of actions, see [actions.json](https://github.com/wst24365888/voice-presentation-control/blob/main/voice_presentation_control/configs/actions.json).

To edit `actions.json`, use `vpc config`.

In `actions.json`, the left-hand side is the sentence that triggers the action, and the right-hand side is the keyboard action to be triggered.

For more actions you can configure, head over to [pyautogui](https://github.com/asweigart/pyautogui).

## Usages

### Usage of `vpc`

`vpc [OPTIONS] COMMAND`

#### Options

| Option          | Description                                          |
| --------------- | ---------------------------------------------------- |
| `-v, --verbose` | Show the detailed log of voice-presentation-control. |
| `--version`     | Show the version of voice-presentation-control.      |
| `--help`        | Show help and exit.                                  |

#### Commands

| Command  | Description                                  |
| -------- | -------------------------------------------- |
| `config` | Edit the config file.                        |
| `mic`    | Check the settings for the microphone input. |
| `start`  | Start vpc.                                   |

### Usage of `vpc mic`

`vpc mic [OPTIONS] COMMAND`

#### Options

| Option   | Description         |
| -------- | ------------------- |
| `--help` | Show help and exit. |

#### Commands

| Command | Description                                                                                         |
| ------- | --------------------------------------------------------------------------------------------------- |
| `list`  | List all audio input devices. You can check the device index you want to use by using this command. |
| `test`  | Test audio environment. Talk and determine the volume threshold by using this command.              |

### Usage of `vpc mic test`

`vpc mic test [OPTIONS]`

#### Options

| Option                     | Description                                                                |
| -------------------------- | -------------------------------------------------------------------------- |
| `-i, --input-device-index` | Set input device index. Check your devices by `vpc mic list`. [default: 1] |
| `-c, --chunk`              | Set record chunk.  [default: 4096]                                         |
| `-r, --rate`               | Set input stream rate.  [default: 44100]                                   |
| `--help`                   | Show help and exit.                                                        |

### Usage of `vpc start`

`vpc start [OPTIONS]`

#### Options

| Option                     | Description                                                                    |
| -------------------------- | ------------------------------------------------------------------------------ |
| `-i, --input-device-index` | Set input device index. Check your devices by `vpc mic list`.  [default: 1]    |
| `-v, --vol-threshold`      | Set volume threshold. Test your environment by `vpc mic test`.  [default: 1000] |
| `-z, --zcr-threshold`      | Set zcr threshold.  [default: 0.075]                                           |
| `-c, --chunk`              | Set record chunk.  [default: 4096]                                             |
| `-r, --rate`               | Set input stream rate.  [default: 44100]                                       |
| `-s, --max-record-seconds` | Set max record seconds if your custom command is long.  [default: 2]           |
| `-l, --language [en, zh]`  | Set language to recognize.  [default: en]                                      |
| `--strict  `               | Use this option for strict mode.                                               |
| `--help`                   | Show help and exit.                                                            |

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- ROADMAP -->

## Roadmap

- [ ] Add more tests.

See the [open issues](https://github.com/wst24365888/voice-presentation-control/issues)
for a full list of proposed features (and known issues).

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- CONTRIBUTING -->

## Contributing

Contributions are what make the open source community such an amazing place to
learn, inspire, and create. Any contributions you make are **greatly
appreciated**.

If you have a suggestion that would make this better, please fork the repo and
create a pull request. You can also simply open an issue with the tag
"enhancement". Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feat/amazing-feature`)
3. Commit your Changes with
   [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
4. Push to the Branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- LICENSE -->

## License

Distributed under the MIT License. See
[LICENSE](https://github.com/wst24365888/voice-presentation-control/blob/main/LICENSE)
for more information.

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- CONTACT -->

## Contact

### Author

- HSING-HAN, WU (Xyphuz)
  - Mail me: xyphuzwu@gmail.com
  - About me: <https://about.xyphuz.com>
  - GitHub: <https://github.com/wst24365888>

### Project Link

- <https://github.com/wst24365888/voice-presentation-control>

<p align="right">(<a href="#top">back to top</a>)</p>

[contributors-shield]: https://img.shields.io/github/contributors/wst24365888/voice-presentation-control.svg?style=for-the-badge
[contributors-url]: https://github.com/wst24365888/voice-presentation-control/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/wst24365888/voice-presentation-control.svg?style=for-the-badge
[forks-url]: https://github.com/wst24365888/voice-presentation-control/network/members
[stars-shield]: https://img.shields.io/github/stars/wst24365888/voice-presentation-control.svg?style=for-the-badge
[stars-url]: https://github.com/wst24365888/voice-presentation-control/stargazers
[issues-shield]: https://img.shields.io/github/issues/wst24365888/voice-presentation-control.svg?style=for-the-badge
[issues-url]: https://github.com/wst24365888/voice-presentation-control/issues
[issues-closed-shield]: https://img.shields.io/github/issues-closed/wst24365888/voice-presentation-control.svg?style=for-the-badge
[issues-closed-url]: https://github.com/wst24365888/voice-presentation-control/issues?q=is%3Aissue+is%3Aclosed
[license-shield]: https://img.shields.io/github/license/wst24365888/voice-presentation-control.svg?style=for-the-badge
[license-url]: https://github.com/wst24365888/voice-presentation-control/blob/main/LICENSE