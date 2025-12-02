import { useParams } from "react-router-dom";
import { useState, useEffect, useMemo } from "react";
import {
  Box,
  Typography,
  List,
  ListItemButton,
  ListItemText,
  Slider
} from "@mui/material";
import axios from "axios";
import PanoViewer from "../components/PanoViewer";
import TerraExplorerControls from "../components/TerraExplorerControls";


function ClusterViewerPage() {
  const { cluster_id } = useParams();
  const [images, setImages] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [loading, setLoading] = useState(true);

  const [timeBounds, setTimeBounds] = useState([0, 0]);
  const [timeRange, setTimeRange] = useState([0, 0]);

  const getImages = async (id) => {
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/images/cluster/${id}`,
        {
          headers: {
            "Content-Type": "application/json"
          }
        }
      );

      if (response.status === 200) {
        const data = response.data;

        const imgs = (data.images || []).map((img) => ({
          ...img,
          createdMs: new Date(img.created).getTime()
        }));

        // Sort by time ascending
        imgs.sort((a, b) => a.createdMs - b.createdMs);

        setImages(imgs);

        if (imgs.length > 0) {
          const times = imgs.map((i) => i.createdMs);
          const minTime = Math.min(...times);
          const maxTime = Math.max(...times);

          setTimeBounds([minTime, maxTime]);
          setTimeRange([minTime, maxTime]);
          setSelectedImage(imgs[0]);
        } else {
          setTimeBounds([0, 0]);
          setTimeRange([0, 0]);
          setSelectedImage(null);
        }
      }
    } catch (error) {
      console.log(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    getImages(cluster_id);
  }, [cluster_id]);

  const handleTimeChange = (event, newValue) => {
    setTimeRange(newValue);
  };

  const filteredImages = useMemo(
    () =>
      images.filter(
        (img) =>
          img.createdMs >= timeRange[0] && img.createdMs <= timeRange[1]
      ),
    [images, timeRange]
  );

  useEffect(() => {
    if (filteredImages.length === 0) {
      setSelectedImage(null);
      return;
    }

    if (
      !selectedImage ||
      !filteredImages.some((img) => img.image_id === selectedImage.image_id)
    ) {
      setSelectedImage(filteredImages[0]);
    }
  }, [filteredImages, selectedImage]);

  const formatTime = (ms) => {
    if (!ms) return "";
    const d = new Date(ms);
    return d.toLocaleTimeString([], {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    });
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflow: 'auto',
        scrollbarWidth: "none",
        "&::-webkit-scrollbar": {
          display: "none"
        }
      }}
    >
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
          Image Cluster: {cluster_id}
        </Typography>
      </Box>

      <Box>
        {loading && <p>Loading...</p>}

        {!loading && images.length > 0 && (
          <>
            {/* Time slider */}
            <Box sx={{ px: 2, pb: 0 }}>
              <Typography variant="body2" sx={{ mb: 1, ml: -1 }}>
                Time range: {formatTime(timeRange[0])} – {formatTime(timeRange[1])}
              </Typography>
              <Slider
                value={timeRange}
                onChange={handleTimeChange}
                min={timeBounds[0]}
                max={timeBounds[1]}
                step={1000} // 1 second
                valueLabelDisplay="off"
                sx={{
                  color: "#0a2463", // navy blue
                  "& .MuiSlider-thumb": {
                    backgroundColor: "#ffffff",
                    border: "2px solid #003366",
                  },
                  "& .MuiSlider-track": {
                    backgroundColor: "#003366",
                  },
                  "& .MuiSlider-rail": {
                    backgroundColor: "#0a246380", // 50% transparent navy
                  },
                }}
              />
            </Box>

            <Box
              sx={{
                display: "flex",
                flexDirection: "row",
                padding: "8px",
                pt: "0px"
              }}
            >
              {/* Left panel: list of images in range */}
              <Box
                sx={{
                  flex: 1,
                  borderRight: "1px solid rgba(255,255,255,0.1)",
                  overflowY: "auto",
                  height: "450px",
                  scrollbarWidth: "none",
                  "&::-webkit-scrollbar": {
                    display: "none"
                  }
                }}
              >
                <List dense>
                  {filteredImages.map((img) => (
                    <ListItemButton
                      key={img.image_id}
                      selected={selectedImage?.image_id === img.image_id}
                      onClick={() => setSelectedImage(img)}
                    >
                      <ListItemText
                        primary={img.name}
                        secondary={img.created}
                      />
                    </ListItemButton>
                  ))}
                </List>
              </Box>

              {/* Right panel: selected image */}
              <Box
                sx={{
                  flex: 3,
                  padding: "8px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 2,
                  height: "450px"
                  //maxHeight: "365px"
                }}
              >
                {!selectedImage && (
                  <Typography variant="body1">
                    No image in the selected time range. Adjust the slider.
                  </Typography>
                )}

                {selectedImage && (
                  selectedImage.image_type !== "pano" ? (
                    <>
                      <Box
                        sx={{
                          flex: 5,
                          //height: "450px",     // matches left panel
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          overflow: "hidden",
                          borderRadius: 1,
                          border: "1px solid rgba(255,255,255,0.1)"
                        }}
                        onClick={() => window.open(selectedImage.signed_url, "_blank", "noopener,noreferrer")}
                      >
                        <Box
                          component="img"
                          src={selectedImage.signed_url}
                          alt={selectedImage.name}
                          sx={{
                            maxWidth: "100%",
                            maxHeight: "100%",
                            objectFit: "contain",
                            cursor: "pointer"
                          }}
                        />
                      </Box>

                      <Typography variant="body2" sx={{ mt: 1, flex: 1, textAlign: "center" }}>
                        Lon: {selectedImage.lon}, Lat: {selectedImage.lat}, Alt:{" "}
                        {selectedImage.alt_m} m, Yaw: {selectedImage.yaw_deg}°, Type: {selectedImage.image_type}
                      </Typography>

                      <TerraExplorerControls selectedImage={selectedImage} />
                    </>
                  ) : (
                    <>
                      <PanoViewer src={selectedImage.signed_url} />
                      <Typography variant="body2" sx={{ mt: 1, flex: 1 }}>
                        Lon: {selectedImage.lon}, Lat: {selectedImage.lat}, Alt:{" "}
                        {selectedImage.alt_m} m, Yaw: {selectedImage.yaw_deg}°, Type: {selectedImage.image_type}
                      </Typography>
                    </>
                  )
                )}
              </Box>
            </Box>
          </>
        )}

        {!loading && images.length === 0 && (
          <Box sx={{ p: 2 }}>
            <Typography variant="body1">
              No images found for cluster_id: {cluster_id}
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  );
}

export default ClusterViewerPage;
