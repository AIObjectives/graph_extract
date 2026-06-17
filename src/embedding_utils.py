import os
import random
import json
import numpy as np
import pandas as pd
import requests

import src.utils as utils

CONFIG = utils.return_config()
OPENAI_API_KEY = utils.resolve_openai_api_key()



class EmbeddingModel:
    """base class for embedding models."""
    def get_embedding(self, text: str) -> list:
        raise NotImplementedError("Must implement in subclass")


class OpenAIEmbeddingModel(EmbeddingModel):
    def __init__(self, model_name: str = "text-embedding-3-large"):
        self.api_key = utils.get_bearer_auth_header()
        self.url = "https://api.openai.com/v1/embeddings"
        self.model_name = model_name

    def get_embedding(self, text: str) -> list:
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.api_key
        }
        data = {
            "input": text,
            "model": self.model_name
        }
        response = requests.post(self.url, headers=headers, json=data)
        if response.status_code != 200:
            raise Exception(f"OpenAI API error {response.status_code}: {response.text}")
        return response.json()["data"][0]["embedding"]



class EmbeddingProjector:
    def __init__(self, model_type: str = "gemini", **kwargs):
        """
        Initialize EmbeddingProjector with specified model type.
        
        Args:
            model_type (str): Either "gemini", "openai", or "qwen"
            **kwargs: Additional arguments for model initialization
        """
        if model_type.lower() == "gemini":
            self.model = GeminiEmbeddingModel(**kwargs)
        elif model_type.lower() == "openai":
            self.model = OpenAIEmbeddingModel(**kwargs)
        elif model_type.lower() == "qwen":
            self.model = QwenEmbeddingModel(**kwargs)
        else:
            raise ValueError(f"Unsupported model type: {model_type}. Use 'gemini', 'openai', or 'qwen'")

    def return_embedding_diff(self, high: list, low: list) -> np.ndarray:
        """Compute vector differences between high and low attribute sets."""
        emb_high = np.mean([self.model.get_embedding(a) for a in high], axis=0)
        emb_low = np.mean([self.model.get_embedding(b) for b in low], axis=0)
        return emb_high - emb_low


    def return_embedding_diff_pairwise(self, high: list, low: list) -> np.ndarray:
        """Compute vector differences between high and low attribute sets, pairwise only."""
        emb_high = [self.model.get_embedding(a) for a in high]
        emb_low = [self.model.get_embedding(b) for b in low]
        return np.mean(np.array(emb_high) - np.array(emb_low), axis=0)
    

    def return_list_embeddings(self, items: list) -> pd.DataFrame:
        """
        Get embeddings for a list of text items.
        """
        df = pd.DataFrame()
        for item in items:
            embedding = self.model.get_embedding(item)
            df.insert(loc=len(df.columns), column=item, value=embedding, allow_duplicates=True)
        return df


    def get_projections(self, item_list: list, emb_vector: np.ndarray) -> pd.DataFrame:
        """
        Project each item's embedding onto a given embedding vector.

        Args:
            item_list (list): List of strings to get embeddings for.
            emb_vector (np.ndarray): Vector to project onto.

        Returns:
            pd.DataFrame: Each item's projection score.
        """
        projection_df = pd.DataFrame(index=item_list, columns=['projection'], data=0.0)

        for item in item_list:
            item_emb = self.model.get_embedding(item)
            projection = np.inner(np.array(item_emb), np.array(emb_vector))
            projection_df.loc[item, "projection"] = float(projection)

        return projection_df
    