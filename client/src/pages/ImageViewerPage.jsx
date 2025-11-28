import { useParams } from "react-router-dom";
import { useState, useEffect } from 'react';
import axios from "axios";
import {
  Box,
  Typography
} from "@mui/material";

function ImageViewerPage() {
  const { id } = useParams()
  const [image, setImage] = useState("")
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
        setImage(data);
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
    <Box>
      <Typography
        fontSize={18}
        fontWeight={600}
        align="left"
        sx={{
          padding: "8px",
          paddingBottom: "0px"
        }}
      >
        Drone Image View
      </Typography>

      {loading && <p>Loading...</p>}
      {!loading && image && (
        <Box
          sx={{
            flex: 3,
            padding: "8px",
            display: "flex",
            flexDirection: "column",
            gap: 2
          }}
        >
          {!image && (
            <Typography variant="body1">
              No image found with image_id: {id}.
            </Typography>
          )}

          {image && (
            <>
              <Typography variant="h6">
                {image.name}
              </Typography>

              <Box
                component="img"
                src={image.signed_url}
                alt={image.name}
                sx={{
                  maxWidth: "100%",
                  maxHeight: "70vh",
                  borderRadius: 1,
                  objectFit: "contain",
                  border: "1px solid rgba(0,0,0,0.1)"
                }}
              />

              <Typography variant="body2" sx={{ mt: 1 }}>
                Lon: {image.lon}, Lat: {image.lat}, Alt:{" "}
                {image.alt_m} m, Yaw: {image.yaw_deg}°
              </Typography>
            </>
          )}
        </Box>
      )}
    </Box>
  )
}

export default ImageViewerPage
