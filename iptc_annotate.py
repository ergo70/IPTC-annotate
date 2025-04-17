#!/usr/bin/env python

"""Recursively annotate JPEG images with IPTC keywords and captions/abstracts using ollama and llava 1.6."""

import logging
import base64
from time import time
from configparser import ConfigParser
from io import BytesIO
from os import walk, path
from argparse import ArgumentParser
from dataclasses import dataclass
from iptcinfo3 import IPTCInfo
from PIL import Image
from llama_index.core.schema import ImageDocument
from llama_index.multi_modal_llms.ollama import OllamaMultiModal

__author__ = "Ernst-Georg Schmid"
__copyright__ = "Copyright 2025, Ernst-Georg Schmid"
__license__ = "MIT"
__version__ = "1.0.0"
__status__ = "Production"


LOGGER = logging.getLogger(__name__)
LLAVA_IMAGE_SIZE = (672, 672)

KW_PROMPT = """Please give five keywords describing this picture, separated by ;. Nothing else, just five keywords separated by semicolons. Thank you!"""
CA_PROMPT = """Please give a short concise abstract describing this picture in one sentence. Nothing else, just the abstract in one sentence. Thank you!"""


@dataclass
class Configuration:
    ollama_model: str
    ollama_base_url: str
    ollama_timeout: float
    directory: str
    overwrite: bool
    language: str


def get_configuration() -> Configuration:
    """Get a valid configuration."""
    argparser = ArgumentParser()
    config_file = ConfigParser()
    argparser.add_argument("""directory""", type=str,
                           help="""Directory to recursively scan for JPEG images""")
    argparser.add_argument("-o", "--overwrite", action="store_true", default=False,
                           help="""Overwrite existing IPTC entries""")
    argparser.add_argument("-l", "--language", action="store", type=str,
                           default="en",
                           help="""Desired output language as ISO 936-1 code""")

    arguments = argparser.parse_args()

    if len(arguments.language) != 2:
        LOGGER.error(
            f"""Language code {arguments.language} is not a proper ISO 936-1 code.""")
        return None

    config_file.read("""iptc_annotate.conf""")
    if config_file:
        try:
            default_section = config_file["""ollama"""]
            ollama_model = default_section.get(
                """model""", """llava:7b""")
            ollama_base_url = default_section.get(
                """base_url""", """http://localhost:11434""")
            ollama_timeout = default_section.getfloat(
                """timeout""", 120.0)
        except KeyError as e:
            LOGGER.warning(
                """No config file iptc_annotate.conf or missing section [ollama]. Proceeding with default settings.""")
            ollama_model = """llava:7b"""
            ollama_base_url = """http://localhost:11434"""
            ollama_timeout = 120.0

    configuration = Configuration(
        ollama_model=ollama_model,
        ollama_base_url=ollama_base_url,
        ollama_timeout=ollama_timeout,
        directory=arguments.directory,
        overwrite=arguments.overwrite,
        language=arguments.language.lower()
    )

    return configuration


def translate(original_text: str = None, target_language: str = """en""") -> str:
    """Translate the text to the requested target language."""
    if target_language == """en""":
        return original_text
    else:
        raise NotImplementedError(
            f"""Translation to {target_language} not implemented yet.""")


def prepare_image_for_llava(image_path: str = None) -> str:
    """Prepare the image for llava."""
    if not image_path or not path.exists(image_path):
        return None

    img = Image.open(image_path)
    # LLava works best with images sized 672x672, 336x1344, or 1344x336
    img = img.resize(LLAVA_IMAGE_SIZE, Image.Resampling.LANCZOS)
    buffered = BytesIO()
    img.save(buffered, format="JPEG", quality=75)
    img_str = base64.b64encode(buffered.getvalue())
    buffered.close()
    img.close()

    return img_str


def annotate_image(image_path: str = None, configuration: Configuration = None) -> None:
    """Annotate a single image with keywords and captions."""

    img_for_llava = prepare_image_for_llava(image_path=image_path)

    if not img_for_llava:
        LOGGER.error(f"""Input image {image_path} not found.""")
        return None

    must_save = False

    llava_multi_modal_llm = OllamaMultiModal(
        model=configuration.ollama_model,
        temperature=0.0,
        request_timeout=configuration.ollama_timeout,
        base_url=configuration.ollama_base_url,
    )

    info = IPTCInfo(image_path, force=True,
                    inp_charset="""utf-8""", out_charset="""utf-8""")
    if not info:
        LOGGER.error(f"""Input image {image_path} not readable.""")
        return None

    if configuration.overwrite:
        old_keywords = None
        old_caption_abstract = None
    else:
        old_keywords = info["""keywords"""]
        old_caption_abstract = info["""caption/abstract"""]

    if old_keywords:
        LOGGER.info(
            f"""Keywords found in {image_path}. Will not overwrite unless --overwrite is set.""")
    else:
        try:
            llava_response = llava_multi_modal_llm.complete(
                prompt=KW_PROMPT,
                image_documents=[ImageDocument(image=img_for_llava)],
            )

            new_keywords = llava_response.text.split(';')
            new_keywords = [translate(original_text=k.strip(), target_language=configuration.language).lower()
                            for k in new_keywords if len(k.strip()) > 0]
            LOGGER.info(f"""New keywords: {new_keywords}.""")
            info["""keywords"""] = new_keywords
            must_save = True
        except Exception as e:
            LOGGER.error(
                f"""Error annotating image {image_path} with keywords: {e}.""")

    if old_caption_abstract:
        LOGGER.info(
            f"""Caption/Abstract found in {image_path}. Will not overwrite unless --overwrite is set.""")
    else:
        try:
            llava_response = llava_multi_modal_llm.complete(
                prompt=CA_PROMPT,
                image_documents=[ImageDocument(image=img_for_llava)],
            )
            new_caption_abstract = llava_response.text.strip()
            new_caption_abstract = translate(
                original_text=new_caption_abstract, target_language=configuration.language)
            LOGGER.info(f"""New caption/abstract: {new_caption_abstract}.""")
            info["""caption/abstract"""] = new_caption_abstract
            must_save = True
        except Exception as e:
            LOGGER.error(
                f"""Error annotating image {image_path} with caption/abstract: {e}.""")

    if must_save:
        info.save(options=["overwrite"])
    else:
        LOGGER.warning(f"""No changes made to {image_path}.""")

    return None


def annotate_images(configuration: Configuration) -> None:
    """Recursively scan a directory for images and annotate them with captions, keywords and abstracts."""
    if not configuration.directory:
        LOGGER.error("""No working directory provided.""")
        return None

    for root, _, filenames in walk(configuration.directory, topdown=True):
        for filename in filenames:
            image_path = path.join(root, filename)
            if image_path.lower().endswith((""".jpg""", """.jpeg""")):
                LOGGER.info(f"Annotating: {image_path}")
                annotate_image(
                    image_path=image_path, configuration=configuration)
            else:
                LOGGER.info(f"Skipping non-JPEG: {image_path}")
                continue

    return None


if __name__ == """__main__""":
    """Main function."""
    start = time()
    logging.basicConfig(level=logging.INFO)
    configuration = get_configuration()
    LOGGER.debug(configuration)
    if configuration:
        annotate_images(configuration=configuration)
        LOGGER.info(
            f"""Completed annotating images in {time() - start:.2f} seconds.""")
    else:
        LOGGER.error("""No configuration found.""")
