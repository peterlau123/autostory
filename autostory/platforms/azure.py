

#!/usr/bin/env python3
"""
Azure Speech Synthesis Module

This module provides Azure Cognitive Services Speech SDK integration for text-to-speech synthesis.

Example usage:
    from autostory.platforms.azure import AzureVoice

    voice = AzureVoice()
    voice.synthesize("Hello, world!")

    # Or from command line:
    python -m autostory.platforms.azure --text "Hello, world!"
"""

import argparse
import os
import sys
from typing import Optional

try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    speechsdk = None


class AzureVoice:
    """
    Azure Speech Synthesis Voice Class

    Handles text-to-speech synthesis using Azure Cognitive Services Speech SDK.
    """

    def __init__(self, key: Optional[str] = None, endpoint: Optional[str] = None):
        """
        Initialize Azure Voice instance.

        Args:
            key: Azure Speech resource key. If None, uses SPEECH_KEY environment variable.
            endpoint: Azure Speech endpoint URL. If None, uses ENDPOINT environment variable.
        """
        if not AZURE_SDK_AVAILABLE:
            raise ImportError(
                "Azure Cognitive Services Speech SDK is not installed. "
                "Install it with: pip install azure-cognitiveservices-speech"
            )

        self.key = key or os.environ.get('SPEECH_KEY')
        self.endpoint = endpoint or os.environ.get('ENDPOINT')

        if not self.key:
            raise ValueError(
                "Azure Speech key is required. Set SPEECH_KEY environment variable or pass key parameter."
            )

        if not self.endpoint:
            raise ValueError(
                "Azure Speech endpoint is required. Set ENDPOINT environment variable or pass endpoint parameter."
            )

    def synthesize(
        self,
        text: str,
        voice: str = 'en-US-Ava:DragonHDLatestNeural',
        output_to_speaker: bool = True
    ) -> bool:
        """
        Synthesize text to speech.

        Args:
            text: Text to synthesize
            voice: Voice name for synthesis
            output_to_speaker: Whether to output to default speaker

        Returns:
            bool: True if synthesis was successful, False otherwise
        """
        try:
            # Configure speech synthesis
            speech_config = speechsdk.SpeechConfig(subscription=self.key, endpoint=self.endpoint)
            speech_config.speech_synthesis_voice_name = voice

            # Configure audio output
            if output_to_speaker:
                audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
            else:
                # Could be extended to save to file in the future
                audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

            # Create speech synthesizer
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=audio_config
            )

            print(f"Synthesizing text: '{text}' using voice: {voice}")

            # Perform speech synthesis
            speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

            # Check result
            if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                print("✓ Speech synthesis completed successfully")
                return True
            elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = speech_synthesis_result.cancellation_details
                print(f"✗ Speech synthesis canceled: {cancellation_details.reason}")

                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    if cancellation_details.error_details:
                        print(f"Error details: {cancellation_details.error_details}")
                        print("Please check your speech resource key and endpoint values.")

                return False
            else:
                print(f"✗ Unexpected result: {speech_synthesis_result.reason}")
                return False

        except Exception as e:
            print(f"✗ Error during speech synthesis: {str(e)}")
            return False

    def get_available_voices(self) -> list:
        """
        Get list of available voices. (Placeholder for future implementation)

        Returns:
            list: List of available voice names
        """
        # This would require additional API calls to Azure to get available voices
        # For now, return some common voices
        return [
            'en-US-Ava:DragonHDLatestNeural',
            'zh-CN-Xiaoxiao:DragonHDFlashLatestNeural',
            'en-US-ZiraRUS',
            'en-GB-SoniaRUS',
        ]


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Azure Speech Synthesis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --text "Hello, world!"
  %(prog)s --text "你好，世界！" --voice "zh-CN-Xiaoxiao:DragonHDFlashLatestNeural"
  %(prog)s --key YOUR_KEY --endpoint YOUR_ENDPOINT --text "Test speech"

Available voices:
  en-US-Ava:DragonHDLatestNeural (default)
  zh-CN-Xiaoxiao:DragonHDFlashLatestNeural
  en-US-ZiraRUS
  en-GB-SoniaRUS
        """
    )

    parser.add_argument(
        '--text', '-t',
        type=str,
        required=True,
        help='Text to synthesize to speech'
    )

    parser.add_argument(
        '--voice', '-v',
        type=str,
        default='en-US-Ava:DragonHDLatestNeural',
        help='Voice name for speech synthesis (default: en-US-Ava:DragonHDLatestNeural)'
    )

    parser.add_argument(
        '--key', '-k',
        type=str,
        default=os.environ.get('SPEECH_KEY'),
        help='Azure Speech resource key (default: SPEECH_KEY environment variable)'
    )

    parser.add_argument(
        '--endpoint', '-e',
        type=str,
        default=os.environ.get('ENDPOINT'),
        help='Azure Speech endpoint URL (default: ENDPOINT environment variable)'
    )

    return parser.parse_args()


def main():
    """Main function for command line usage."""
    try:
        # Parse arguments
        args = parse_arguments()

        # Create Azure Voice instance
        voice = AzureVoice(key=args.key, endpoint=args.endpoint)

        # Perform speech synthesis
        success = voice.synthesize(args.text, args.voice)

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\nOperation canceled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
