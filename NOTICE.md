# Third-party notices

Agent Voice Kit is independent software released under the MIT License.

## edge-tts

This project depends on [`edge-tts`](https://github.com/rany2/edge-tts), an independent Python client maintained by rany2 and contributors. Per its upstream license file, all files except `src/edge_tts/srt_composer.py` are distributed under the GNU Lesser General Public License v3.0 (LGPL-3.0); that file is distributed under the MIT License. Agent Voice Kit does not copy or modify upstream source code; it installs and imports the published package as a separate dependency.

- Source: https://github.com/rany2/edge-tts
- License: https://github.com/rany2/edge-tts/blob/master/LICENSE
- PyPI: https://pypi.org/project/edge-tts/

## Microsoft service and voices

The generated speech comes from Microsoft Edge's online Read Aloud service. Microsoft, Edge, Azure and the voice names are trademarks or service identifiers of their respective owner. This project is not affiliated with, endorsed by or supported by Microsoft.

The consumer endpoint used by `edge-tts` is not a contracted API for this project. Availability, behavior and terms can change without notice. Review the applicable Microsoft terms before production or commercial use.

## FFmpeg

FFmpeg/ffprobe are external runtime programs used for conversion and verification. They are not bundled with this repository. Their licensing depends on the build distributed by your operating system or package manager: https://ffmpeg.org/legal.html

## Optional official providers

The optional `azure` route calls the official Azure Speech REST API, and the optional `openai` route calls the official OpenAI Audio Speech REST API. No provider SDK code is bundled. Users supply their own accounts, credentials and billing relationship and must follow the applicable provider terms.

- Azure Speech documentation: https://learn.microsoft.com/azure/ai-services/speech-service/how-to-speech-synthesis
- OpenAI text-to-speech documentation: https://developers.openai.com/api/docs/guides/text-to-speech
