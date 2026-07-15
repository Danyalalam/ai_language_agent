---
layout: Conceptual
title: How to use the Voice Live API - Foundry Tools | Microsoft Learn
canonicalUrl: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live-how-to
breadcrumb_path: ../../breadcrumb/azure-ai/toc.json
feedback_help_link_url: https://learn.microsoft.com/answers/tags/55/azure-speech/
feedback_help_link_type: get-help-at-qna
feedback_product_url: https://feedback.azure.com/d365community/forum/09041fae-0b25-ec11-b6e6-000d3a4f0858?c=21041fae-0b25-ec11-b6e6-000d3a4f0858
feedback_system: Standard
permissioned-type: public
recommendations: true
recommendation_types:
- Training
- Certification
uhfHeaderId: azure-ai-foundry
ms.suite: office
author: PatrickFarley
learn_banner_products:
- azure
manager: mcleans
ms.author: pafarley
ms.collection: ce-skilling-ai-copilot
ms.update-cycle: 180-days
ms.service: azure-speech-foundry-tools
description: Learn how to use the Voice Live API for real-time voice agents.
reviewer: patrickfarley
ms.reviewer: pafarley
ms.topic: how-to
ms.date: 2026-05-25T00:00:00.0000000Z
ai-usage: ai-assisted
ms.custom: references_regions
locale: en-us
document_id: d0b86450-8913-3eb1-5480-9071181fd1ff
document_version_independent_id: 8d82ede5-d430-be8d-5ab5-ab4f064129e7
updated_at: 2026-06-23T22:11:00.0000000Z
original_content_git_url: https://github.com/MicrosoftDocs/azure-ai-docs-pr/blob/live/articles/ai-services/speech-service/voice-live-how-to.md
gitcommit: https://github.com/MicrosoftDocs/azure-ai-docs-pr/blob/946ccedc0a41ac19b7b3c66a2359485e1457d258/articles/ai-services/speech-service/voice-live-how-to.md
git_commit_id: 946ccedc0a41ac19b7b3c66a2359485e1457d258
site_name: Docs
depot_name: Learn.azure-ai
page_type: conceptual
toc_rel: toc.json
word_count: 3182
asset_id: ai-services/speech-service/voice-live-how-to
moniker_range_name: 
monikers: []
item_type: Content
source_path: articles/ai-services/speech-service/voice-live-how-to.md
cmProducts:
- https://authoring-docs-microsoft.poolparty.biz/devrel/68ec7f3a-2bc6-459f-b959-19beb729907d
- https://authoring-docs-microsoft.poolparty.biz/devrel/a8711e05-df51-442a-970f-935304535b39
- https://microsoft-devrel.poolparty.biz/DevRelOfferingOntology/de19c5b8-e208-412e-9238-db3f631dea5b
spProducts:
- https://authoring-docs-microsoft.poolparty.biz/devrel/90370425-aca4-4a39-9533-d52e5e002a5d
- https://authoring-docs-microsoft.poolparty.biz/devrel/3d3c20d8-79ed-4203-aee0-ffb9c9bafe72
- https://microsoft-devrel.poolparty.biz/DevRelOfferingOntology/ea7bf5d6-7154-4ba9-8ebc-59117ccacd49
platformId: 5b777173-b696-dcce-c3da-fed7d1944fd7
---

# How to use the Voice Live API - Foundry Tools | Microsoft Learn

The Voice Live API provides a capable WebSocket interface compared to the [Azure OpenAI Realtime API](../../ai-foundry/openai/how-to/realtime-audio).

Unless otherwise noted, the Voice Live API uses the [same events](/en-us/azure/ai-foundry/openai/realtime-audio-reference?context=/azure/ai-services/speech-service/context/context) as the Azure OpenAI Realtime API. This document provides a reference for the event message properties that are specific to the Voice Live API.

Tip

In most cases, use [Voice Live API with WebRTC](voice-live-webrtc) for real-time audio streaming in client-side applications such as a web application or mobile app. WebRTC is designed for low-latency, real-time audio streaming scenarios.

## Supported models and regions

For a table of supported models and regions, see the [Voice Live API overview](voice-live#supported-models-and-regions).

## Authentication

A [Microsoft Foundry resource](../multi-service-resource) or a [Azure Speech in Foundry Tools Services resource](https://portal.azure.com/#create/Microsoft.CognitiveServicesSpeechServices) is required to use the Voice Live API.

Note

Using Voice Live API is optimized for Microsoft Foundry resources. We recommend using Microsoft Foundry resources for full feature availability and best Microsoft Foundry integration experience.**Azure Speech Services resources** don't support Microsoft Foundry Agent Service integration and bring-your-own-model (BYOM).

### WebSocket endpoint

The WebSocket endpoint for the Voice Live API is `wss://<your-ai-foundry-resource-name>.services.ai.azure.com/voice-live/realtime?api-version=2026-04-10` or, for older resources, `wss://<your-ai-foundry-resource-name>.cognitiveservices.azure.com/voice-live/realtime?api-version=2026-04-10`. The endpoint is the same for all models. The only difference is the required `model` query parameter, or, when using the Agent service, the `agent_id` and `project_id` parameters.

For example, an endpoint for a resource with a custom domain would be `wss://<your-ai-foundry-resource-name>.services.ai.azure.com/voice-live/realtime?api-version=2026-04-10&model=gpt-realtime`

### Credentials

The Voice Live API supports two authentication methods:

- **Microsoft Entra** (recommended): Use token-based authentication for a Microsoft Foundry resource. Apply a retrieved authentication token using a `Bearer` token with the `Authorization` header.
- **API key**: An `api-key`can be provided in one of two ways:
    - Using an `api-key` connection header on the prehandshake connection. This option isn't available in a browser environment.
    - Using an `api-key` query string parameter on the request URI. Query string parameters are encrypted when using https/wss.

For the recommended keyless authentication with Microsoft Entra ID, you need to:

- Assign the `Cognitive Services User` and `Foundry User` role to your user account or a managed identity. You can assign roles in the Azure portal under **Access control (IAM)** &gt; **Add role assignment**.

    Important

    The Foundry RBAC roles were recently renamed. **Foundry User**, **Foundry Owner**, **Foundry Account Owner**, and **Foundry Project Manager** were previously named Azure AI User, Azure AI Owner, Azure AI Account Owner, and Azure AI Project Manager. You might still see the previous names in some places while the rename rolls out. The role IDs and core permissions are unchanged by the rename.
- Generate a token using the Azure CLI or Azure SDKs. The token must be generated with the `https://ai.azure.com/.default` scope, or the legacy `https://cognitiveservices.azure.com/.default` scope.
- Use the token in the `Authorization` header of the WebSocket connection request, with the format `Bearer <token>`.

## Session configuration

Often, the first event sent by the caller on a newly established Voice Live API session is the [`session.update`](../openai/realtime-audio-reference?context=/azure/ai-services/speech-service/context/context#realtimeclienteventsessionupdate) event. This event controls a wide set of input and output behavior, with output and response generation properties then later overridable using the [`response.create`](../openai/realtime-audio-reference?context=/azure/ai-services/speech-service/context/context#realtimeclienteventresponsecreate) event.

Here's an example `session.update` message that configures several aspects of the session, including turn detection, input audio processing, and voice output. Most session parameters are optional and can be omitted if not needed.

```json
{
    "instructions": "You are a helpful AI assistant responding in natural, engaging language.",
    "turn_detection": {
        "type": "azure_semantic_vad",
        "silence_duration_ms": 500,
    },
    "input_audio_noise_reduction": {"type": "azure_deep_noise_suppression"},
    "input_audio_echo_cancellation": {"type": "server_echo_cancellation"},
    "voice": {
        "name": "en-US-Ava:DragonHDLatestNeural",
        "type": "azure-standard",
        "temperature": 0.8,
    },
}
```

Important

The `"instructions"` property isn't supported when you're using a custom agent.

The server responds with a [`session.updated`](../openai/realtime-audio-reference?context=/azure/ai-services/speech-service/context/context#realtimeservereventsessionupdated) event to confirm the session configuration.

## Session Properties

The following sections describe the properties of the `session` object that can be configured in the `session.update` message.

Tip

For comprehensive descriptions of supported events and properties, see the [Azure OpenAI Realtime API events reference documentation](../openai/realtime-audio-reference?context=/azure/ai-services/speech-service/context/context). This document provides a reference for the event message properties that are enhancements via the Voice Live API.

### Input audio properties

You can use input audio properties to configure the input audio stream.

| Property | Type | Required or optional | Description |
| --- | --- | --- | --- |
| `input_audio_sampling_rate` | integer | Optional | The sampling rate of the input audio.The supported values are `16000` and `24000`. The default value is `24000`. |
| `input_audio_echo_cancellation` | object | Optional | Enhances the input audio quality by removing the echo from the model's own voice without requiring any client-side echo cancellation.Set the `type` property of `input_audio_echo_cancellation` to enable echo cancellation.The supported value for `type` is `server_echo_cancellation`, which is used when the model's voice is played back to the end-user through a speaker, and the microphone picks up the model's own voice. |
| `input_audio_noise_reduction` | object | Optional | Enhances the input audio quality by suppressing or removing environmental background noise.Set the `type` property of `input_audio_noise_reduction` to enable noise suppression.The supported value for `type` is `azure_deep_noise_suppression`, which optimizes for speakers closest to the microphone.You can set this property to `near_field` or `far_field` if you're using the [Azure OpenAI Realtime API](../../ai-foundry/openai/realtime-audio-reference#realtimeaudioinputaudionoisereductionsettings). |

Here's an example of input audio properties in a session object:

```json
{
    "input_audio_sampling_rate": 24000,
    "input_audio_noise_reduction": {"type": "azure_deep_noise_suppression"},
    "input_audio_echo_cancellation": {"type": "server_echo_cancellation"},
}
```

#### Noise suppression and echo cancellation

Noise suppression enhances the input audio quality by suppressing or removing environmental background noise. Noise suppression helps the model understand the end-user with higher accuracy and improves accuracy of signals like interruption detection and end-of-turn detection.

Server echo cancellation enhances the input audio quality by removing the echo from the model's own voice. In this way, client-side echo cancellation isn't required. Server echo cancellation is useful when the model's voice is played back to the end-user through a speaker. This helps avoiding the microphone picking up the model's own voice.

Note

The service assumes the client plays response audio as soon as it receives them. If playback is delayed for more than two seconds, echo cancellation quality is impacted.

## Conversational enhancements

The Voice Live API offers conversational enhancements to provide robustness to the natural end-user conversation flow.

### Turn Detection Parameters

Turn detection is the process of detecting when the end-user started or stopped speaking. The Voice Live API builds on the Azure OpenAI Realtime API `turn_detection` property to configure turn detection. The `azure_semantic_vad` and `azure_multilingual_semantic_vad` types are key differentiators between the Voice Live API and the Azure OpenAI Realtime API.

| Property | Type | Required or optional | Description |
| --- | --- | --- | --- |
| `type` | string | Optional | The type of turn detection system to use. Type `server_vad` detects start and end of speech based on audio volume.Type `semantic_vad` uses a semantic classifier to detect when the user has finished speaking, based on the words they have uttered. This type can only be used with the *gpt-realtime* and *gpt-realtime-mini* models.Type `azure_semantic_vad` and `azure_semantic_vad_multilingual` also detects start and end of speech based on semantic meaning and can be used with *all models*. Further Azure semantic voice activity detection (VAD) can also improve turn detection by removing filler words to reduce the false alarm rate of barge-in.The default value is `server_vad`. |
| `threshold` | float | Optional | Activation threshold (0.0–1.0). A higher threshold requires a higher confidence signal of the user trying to speak (default: 0.5). Available with types `server_vad`, `azure_semantic_vad`, and `azure_semantic_vad_multilingual`. |
| `prefix_padding_ms` | integer | Optional | The amount of audio, measured in milliseconds, to include before the start of speech detection signal. Starting with API version `2026-04-10`, the default is 400 for `server_vad` and 420 for `azure_semantic_vad` and `azure_semantic_vad_multilingual`. For earlier API versions, the default is 300 for all types. |
| `speech_duration_ms` | integer | Optional | The duration of user's speech audio, measured in milliseconds, required to start detection. The default value is 200 ms for `server_vad` and 80 ms for `azure_semantic_vad` and `azure_semantic_vad_multilingual`. |
| `silence_duration_ms` | integer | Optional | The duration of user's silence, measured in milliseconds, to detect the end of speech (default: 500). |
| `remove_filler_words` | boolean | Optional | Determines whether to remove filler words to reduce the false alarm rate of barge-in.To enable it the property must be set to `true`. The detected filler words in English are `['ah', 'umm', 'mm', 'uh', 'huh', 'oh', 'yeah', 'hmm']`. The service ignores these words when there's an ongoing response. Remove filler words feature assumes the client plays response audio as soon as it receives them.The default value is `false`. |
| `languages` | string[] | Optional | Language will be used to improve the `remove_filler_words` accuracy by reducing the applied languages (default: none). The type `azure_semantic_vad` primarily supports English. Type `azure_semantic_vad_multilingual` is also available to support a wider variety of languages: English, Spanish, French, Italian, German (DE), Japanese, Portuguese, Chinese, Korean, Hindi. Other languages will be ignored. Available with types `azure_semantic_vad` and `azure_semantic_vad_multilingual`. |
| `create_response` | boolean | Optional | Enable or disable whether a response is generated (default: true). |
| `eagerness` | string | Optional | This is a way to control how eager the model is to interrupt the user, tuning the maximum wait timeout. Only available with type `semantic_vad`. In transcription mode, even if the model doesn't reply, it affects how the audio is chunked.The following values are allowed:- `auto` (default) is equivalent to `medium`,- `low` will let the user take their time to speak,- `high` will chunk the audio as soon as possible.If you want the model to respond more often in conversation mode, or to return transcription events faster in transcription mode, you can set eagerness to `high`.On the other hand, if you want to let the user speak uninterrupted in conversation mode, or if you would like larger transcript chunks in transcription mode, you can set eagerness to `low`. |
| `interrupt_response` | boolean | Optional | Enable or disable barge-in interruption (default: true). Only available with type `azure_semantic_vad` and `azure_semantic_vad_multilingual`. |
| `auto_truncate` | boolean | Optional | Auto-truncate on interruption (default: false). |

## Audio input transcription

The Voice Live API supports multiple transcription models for input audio. Set the `model` field in `input_audio_transcription` to choose one. The available models depend on which chat model you're using:

| Transcription model | Compatible chat models | Description |
| --- | --- | --- |
| `azure-speech` | All non-multimodal models and agents | Azure speech to text. Automatically active with non-multimodal models. Supports [phrase list and custom speech](voice-live-how-to-customize). |
| `mai-transcribe` | All non-multimodal models and agents | MAI Transcribe speech recognition model (preview). |
| `whisper-1` | `gpt-realtime`, `gpt-realtime-mini` | OpenAI Whisper transcription model. |
| `gpt-4o-transcribe` | `gpt-realtime`, `gpt-realtime-mini` | GPT-4o based transcription model. |
| `gpt-4o-mini-transcribe` | `gpt-realtime`, `gpt-realtime-mini` | GPT-4o mini based transcription model. |
| `gpt-4o-transcribe-diarize` | `gpt-realtime`, `gpt-realtime-mini` | GPT-4o transcription with diarization. |

For supported languages per model, see [Voice Live API supported languages](voice-live-language-support?tabs=speechinput).

### Azure speech to text

Azure speech to text is automatically active when you're using a non-multimodal model. You can explicitly configure it by setting `model` to `azure-speech`:

```json
{
    "session": {
        "input_audio_transcription": {
            "model": "azure-speech",
            "language": "en"
        }
    }
}
```

For speech input customization options such as phrase list and custom speech, see [How to customize Voice Live input and output](voice-live-how-to-customize).

### MAI Transcribe (preview)

MAI Transcribe is a transcription model that you can use as an alternative to `azure-speech` with any text-based chat model or agent (for example, `gpt-4.1`). Enable it by setting `input_audio_transcription.model` to `mai-transcribe` in a `session.update` message:

```json
{
  "type": "session.update",
  "session": {
    "input_audio_transcription": {
      "model": "mai-transcribe"
    },
    "modalities": ["text", "audio"],
    "instructions": "You are a helpful assistant.",
    "turn_detection": {
      "type": "azure_semantic_vad_multilingual"
    }
  }
}
```

The following example shows the same configuration with the Voice Live SDK for Python:

```python
from azure.ai.voicelive.aio import connect
from azure.ai.voicelive.models import (
    AudioInputTranscriptionOptions,
    AzureSemanticVadMultilingual,
    AzureStandardVoice,
    Modality,
    RequestSession,
)
from azure.identity.aio import DefaultAzureCredential

async with connect(
    endpoint="https://<your-resource>.services.ai.azure.com/",
    credential=DefaultAzureCredential(),
    model="gpt-4.1",
) as conn:
    await conn.session.update(
        session=RequestSession(
            input_audio_transcription=AudioInputTranscriptionOptions(
                model="mai-transcribe",
            ),
            voice=AzureStandardVoice(name="en-US-AvaNeural"),
            modalities=[Modality.TEXT, Modality.AUDIO],
            instructions="You are a helpful assistant.",
            turn_detection=AzureSemanticVadMultilingual(),
        )
    )
```

Note

For production applications, use `DefaultAzureCredential` from `azure.identity` for keyless authentication. You can also use `AzureKeyCredential` from `azure.core.credentials` with an API key. For complete SDK examples in C#, JavaScript, and Java, see the [Voice Live quickstart](voice-live-quickstart).

### OpenAI transcription models

When using `gpt-realtime` or `gpt-realtime-mini`, you can use OpenAI transcription models (`whisper-1`, `gpt-4o-transcribe`, `gpt-4o-mini-transcribe`, or `gpt-4o-transcribe-diarize`). These models also support an optional `prompt` parameter to guide transcription:

```json
{
    "session": {
        "input_audio_transcription": {
            "model": "gpt-4o-transcribe",
            "language": "en",
            "prompt": "Expected terminology: Azure, Foundry, WebSocket"
        }
    }
}
```

## Audio output through Azure text to speech

You can use the `voice` parameter to specify a standard or custom voice. The voice is used for audio output.

The `voice` object has the following properties:

| Property | Type | Required or optional | Description |
| --- | --- | --- | --- |
| `name` | string | Required | Specifies the name of the voice. For example, `en-US-AvaNeural`. |
| `type` | string | Required | Configuration of the type of Azure voice between `azure-standard` and `azure-custom`. |
| `temperature` | number | Optional | Specifies temperature applicable to Azure HD voices. Higher values provide higher levels of variability in intonation, prosody, etc. |

See [How to customize Voice Live input and output](voice-live-how-to-customize) learn more about speech output customization configuration.

### Azure standard voices

Here's a partial message example for a standard (`azure-standard`) voice:

```json
{
  "voice": {
    "name": "en-US-AvaNeural",
    "type": "azure-standard"
  }
}
```

For the full list of standard voices, see [Language and voice support for the Speech service](language-support?tabs=tts).

### Azure high definition voices

Here's an example `session.update` message for a standard high definition voice:

```json
{
  "voice": {
    "name": "en-US-Ava:DragonHDLatestNeural",
    "type": "azure-standard",
    "temperature": 0.8 // optional
  }
}
```

For the full list of standard high definition voices, see [high definition voices documentation](high-definition-voices#supported-azure-speech-hd-voices).

Note

High definition voices are currently supported in the following regions only: southeastasia, centralindia, swedencentral, westeurope, eastus, eastus2, westus2

### Speaking rate

Use the `rate` string property to adjust the speaking speed for any standard Azure text to speech voices and custom voices.

The rate value should range from 0.5 to 1.5, with higher values indicating faster speeds.

```json
{
  "voice": {
    "name": "en-US-Ava:DragonHDLatestNeural",
    "type": "azure-standard",
    "temperature": 0.8, // optional
    "rate": "1.2"
  }
}
```

### Audio timestamps

When you use Azure voices, and `output_audio_timestamp_types` is configured, the service returns the `response.audio_timestamp.delta` in the response, and `response.audio_timestamp.done` when the all timestamps message are returned.

To configure the audio timestamps, you can set the `output_audio_timestamp_types` in the session.update message.

```json
{
    "session": {
        "output_audio_timestamp_types": ["word"]
    }
}
```

Service returns the audio timestamps in the response when the audio is generated.

```json
{
    "event_id": "<event_id>",
    "type": "response.audio_timestamp.delta",
    "response_id": "<response_id>",
    "item_id": "<item_id>",
    "output_index": 0,
    "content_index": 0,
    "audio_offset_ms": 490,
    "audio_duration_ms": 387,
    "text": "end",
    "timestamp_type": "word"
}
```

And a `response.audio_timestamp.done` message is sent when all timestamps are returned.

```json
{
    "event_id": "<event_id>",
    "type": "response.audio_timestamp.done",
    "response_id": "<response_id>",
    "item_id": "<item_id>",
}
```

### Viseme

A viseme is the visual description of a phoneme in spoken language. It defines the position of the face and mouth while a person is speaking.

You can use Azure standard voice or Azure custom voice with `animation.outputs` set to `{"viseme_id"}`. The service returns the `response.animation_viseme.delta` in the response and `response.animation_viseme.done` when all viseme messages are returned.

Tip

For more information about viseme via Speech Synthesis Markup Language (SSML), see [viseme element documentation](speech-synthesis-markup-voice#viseme-element).

To configure the viseme, you can set the `animation.outputs` in the `session.update` message. The `animation.outputs` parameter is optional. It configures which animation outputs should be returned. Currently, it only supports `viseme_id`.

```json
{
  "type": "session.update",
  "event_id": "your-session-id",
  "session": {
    "voice": {
      "name": "en-US-AvaNeural",
      "type": "azure-standard",
    },
    "modalities": ["text", "audio"],
    "instructions": "You are a helpful AI assistant responding in natural, engaging language.",
    "turn_detection": {
        "type": "server_vad"
    },
    "output_audio_timestamp_types": ["word"], // optional
    "animation": {
        "outputs": ["viseme_id"], // optional
    },
  }
}
```

The `output_audio_timestamp_types` parameter is optional. It configures which audio timestamps should be returned for generated audio. Currently, it only supports `word`.

The service returns the viseme alignment in the response when the audio is generated.

```json
{
    "event_id": "<event_id>",
    "type": "response.animation_viseme.delta",
    "response_id": "<response_id>",
    "item_id": "<item_id>",
    "output_index": 0,
    "content_index": 0,
    "audio_offset_ms": 455,
    "viseme_id": 20
}
```

And a `response.animation_viseme.done` message is sent when all viseme messages are returned.

```json
{
    "event_id": "<event_id>",
    "type": "response.animation_viseme.done",
    "response_id": "<response_id>",
    "item_id": "<item_id>",
}
```

## azure-realtime model

The `azure-realtime` model is a dedicated real-time model that uses a curated set of native voices designed for natural-sounding real-time speech output.

Note

The `azure-realtime` model requires API version `2026-01-01-preview` or later.

### Voice configuration

Specify the voice as a structured object with `type` set to `azure-realtime-native` and `name` set to one of the supported voice names:

```json
{
  "type": "session.update",
  "session": {
    "voice": {
      "type": "azure-realtime-native",
      "name": "ava"
    },
    "modalities": ["text", "audio"],
    "instructions": "You are a helpful assistant."
  }
}
```

### Supported voices

The following `azure-realtime-native` voice names are supported:

| Voice name | Description |
| --- | --- |
| `aarti` | Azure Speech native voice |
| `andrew` | Azure Speech native voice |
| `ava` | Azure Speech native voice (default) |
| `denise` | Azure Speech native voice |
| `elsa` | Azure Speech native voice |
| `florian` | Azure Speech native voice |
| `francisca` | Azure Speech native voice |
| `meera` | Azure Speech native voice |
| `ximena` | Azure Speech native voice |
| `xiaoxiao` | Azure Speech native voice |
| `yunxi` | Azure Speech native voice |

If you don't specify a voice, `ava` is used by default. The default appears in both the `session.created` response and subsequent `session.updated` responses.

## Azure text to speech avatar

[Text to speech avatar](text-to-speech-avatar/what-is-text-to-speech-avatar) converts text into a digital video of a photorealistic human (either a standard avatar or a [custom text to speech avatar](text-to-speech-avatar/what-is-custom-text-to-speech-avatar)) speaking with a natural-sounding voice.

You can use the `avatar` parameter to specify a standard or custom avatar. The avatar is synchronized with the audio output.

An `avatar` parameter can be specified to enable avatar output that is synchronized with the audio output:

```json
{
  "session": {
    "avatar": {
      "character": "lisa",
      "style": "casual-sitting",
      "customized": false,
      "ice_servers": [
        {
          "urls": ["REDACTED"],
          "username": "",
          "credential": ""
        }
      ],
      "video": {
        "bitrate": 2000000,
        "codec": "h264",
        "crop": {
          "top_left": [560, 0],
          "bottom_right": [1360, 1080],
        },
        "resolution": {
          "width": 1080,
          "height": 1920,
        },
        "background": {
          "color": "#00FF00FF"
          // "image_url": "https://example.com/example.jpg"
        }
      }
    }
  }
}
```

The `ice_servers` field is optional. If you don't specify it, the service returns the server-specific ICE servers in `session.updated` response. And you need to use the server-specific ICE servers to generate the local ICE candidates.

Send the client SDP after ICE candidates are gathered.

```json
{
    "type": "session.avatar.connect",
    "client_sdp": "your-client-sdp"
}
```

And the service responds with the server SDP.

```json
{
    "type": "session.avatar.connecting",
    "server_sdp": "your-server-sdp"
}
```

Then you can connect the avatar with the server SDP.

Refer to this sample code [use avatar in Voice live API](https://github.com/microsoft-foundry/voicelive-samples/tree/main/javascript/voice-live-avatar) for more details.

### Use a photo avatar

A [photo avatar](text-to-speech-avatar/what-is-text-to-speech-avatar) generates a talking-head video from a single image. Voice Live supports both standard photo avatars (provided by Microsoft) and custom photo avatars (created from your own image). To use a photo avatar, set `type` to `photo-avatar` and `model` to the base model that drives it (currently `vasa-1`). For a standard photo avatar, set `character` to the photo avatar character name (for the list, see [Talking heads](text-to-speech-avatar/standard-avatars#talking-heads)). For a custom photo avatar, set `character` to your custom photo avatar name and set `customized` to `true`.

Use the optional `scene` object to adjust the avatar's zoom, position, rotation, and movement amplitude. For the meaning and ranges of each scene field, see [Set avatar scene for photo avatar](text-to-speech-avatar/real-time-synthesis-avatar#set-avatar-scene-for-photo-avatar).

Here's an example `avatar` object for a standard photo avatar:

```json
{
  "session": {
    "avatar": {
      "type": "photo-avatar",
      "model": "vasa-1",
      "character": "anika",
      "video": {
        "codec": "h264",
        "resolution": {
          "width": 1920,
          "height": 1080
        }
      },
      "scene": {
        "zoom": 1.0,
        "position_x": 0.0,
        "position_y": 0.0,
        "rotation_x": 0.0,
        "rotation_y": 0.0,
        "rotation_z": 0.0,
        "amplitude": 0.6
      }
    }
  }
}
```

To use a custom photo avatar, set `character` to your custom photo avatar name and set `customized` to `true`:

```json
{
  "session": {
    "avatar": {
      "type": "photo-avatar",
      "model": "vasa-1",
      "character": "your-custom-photo-avatar-name",
      "customized": true
    }
  }
}
```

Note

Azure text to speech avatar is currently supported in limited regions. For the current list of supported regions, see the [Speech service regions table](regions?tabs=ttsavatar).