import { useParams } from "react-router-dom";
import { useState, useEffect } from 'react';
import axios from "axios";

function ViewerPage() {
  const { id } = useParams()
  const [imageUrl, setImageUrl] = useState([])

  const getImageUrl = async (image_id) => {
    try {
      const response = await axios.get(
        `https://heathgate.ngis.com.au/skyline-fusion-api/images/${image_id}`,
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
    }
  }

  useEffect(() => {
    getImageUrl(id);
  }, [id]);

  return (
    <div style={{ padding: '1.5rem' }}>
      <h1>Viewer</h1>
      <p>Showing viewer for project/image ID: {imageUrl}</p>
      <img
        src={imageUrl}
        alt="drone image from google cloud storage"
        width={400}
        loading="lazy"
        crossOrigin="anonymous"
      />
    </div>
  )
}

export default ViewerPage
