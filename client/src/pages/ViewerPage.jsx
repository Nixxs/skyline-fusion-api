import { useParams } from "react-router-dom";
import { useState, useEffect } from 'react';
import axios from "axios";

function ViewerPage() {
  const { id } = useParams()
  const [imageUrl, setImageUrl] = useState("")
  const [loading, setLoading] = useState(true);

  const getImageUrl = async (image_id) => {
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/image/${image_id}`,
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (response.status === 200) {
        const data = response.data;
        setImageUrl(data.signed_url);
      }
    } catch (error) {
      console.log(error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    getImageUrl(id);
  }, [id]);

  return (
    <div style={{ padding: '1.5rem' }}>
      <h1>Viewer</h1>
      <p>Showing viewer for project/image ID: {imageUrl}</p>

      {loading && <p>Loading...</p>}

      {!loading && imageUrl && (
        <img
          src={imageUrl}
          alt="drone image from google cloud storage"
          width={400}
          loading="lazy"
          crossOrigin="anonymous"
        />
      )}
    </div>
  )
}

export default ViewerPage
