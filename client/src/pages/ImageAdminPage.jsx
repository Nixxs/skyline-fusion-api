import { useState } from 'react';
import axios from "axios";
import {
  Box,
  Typography,
  Button,
  TextField,
  FormControlLabel,
  Checkbox,
  CircularProgress
} from "@mui/material";
import FileUploadOutlinedIcon from '@mui/icons-material/FileUploadOutlined';
import Tooltip from '@mui/material/Tooltip';

function ImageAdminPage() {
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState(null);
  const [maxDistance, setMaxDistance] = useState(200);
  const [maxYawDiff, setMaxYawDiff] = useState(90);
  const [resetExisting, setResetExisting] = useState(true);
  const [responseData, setResponseData] = useState(null);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];
    setFile(selectedFile || null);


    console.log("file set");
  }

  const handleUpload = async (event) => {
    event.preventDefault();
    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/images`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      if (response.status === 201) {
        setResponseData(response.data);

        console.log("submitted file:", file.name)
        console.log(response.data);
      }
    } catch (error) {
      console.error(error);
      setResponseData(error);
    } finally {
      setLoading(false);
      setFile(null)
    }
  }

  const handleClustering = async (event) => {
    event.preventDefault();
    setLoading(true);

    const payload = {
      max_distance_m: Number(maxDistance),
      max_yaw_diff_deg: Number(maxYawDiff),
      reset_existing: resetExisting,
    }
    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/images/cluster`,
        payload,
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (response.status === 200) {
        setResponseData(response.data);
      }
    } catch (error) {
      console.log(error);
      setResponseData(error);
    } finally {
      setLoading(false);
    }

    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/images/cluster`,
        payload,
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (response.status === 200) {
        setResponseData(response.data);
      }
    } catch (error) {
      console.log(error);
    } finally {
      setLoading(false);
      console.log("sent payload", payload);
    }
  }

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        padding: 1,
        maxWidth: 900
      }}
    >
      <Box
        sx={{
          mb: 1,
          mt: 0
        }}
      >
        <Typography
          fontSize={18}
          fontWeight={600}
        >
          Drone Image Admin
        </Typography>
      </Box>
      <Box
        sx={{
          display: "flex",
          flexDirection: "row"
        }}
      >
        <Box
          sx={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            maxWidth: 380,
            position: "relative"
          }}
        >
          <Typography
            fontWeight={400}
            fontSize={16}
            sx={{
              variant: "label",
              pt: "6px",
              mr: 1,
              mb: 1
            }}
          >
            Upload Images:
          </Typography>
          <Box
            sx={{
              flexDirection: "row",
              display: "flex"
            }}
          >
            <Tooltip title="Select a .zip of drone images (jpeg,png,tif)">
              <Button
                variant="outlined"
                component="label"
                sx={{
                  flex: 1
                }}
              >
                <FileUploadOutlinedIcon />
                {file ? file.name : "Browse"}
                <input
                  type="file"
                  hidden
                  accept=".zip,application/zip,application/x-zip-compressed"
                  onChange={handleFileChange}
                />
              </Button>
            </Tooltip>
            <Tooltip title="select a file first, then upload from here">
              <Button
                disabled={file ? false : true}
                variant="contained"
                component="label"
                sx={{
                  ml: 1,
                  flex: 1
                }}
                onClick={handleUpload}
              >
                Upload
              </Button>
            </Tooltip>
          </Box>

          <Typography
            fontWeight={400}
            fontSize={16}
            sx={{
              variant: "label",
              pt: "6px",
              mr: 1,
              mb: 1,
              mt: 2
            }}
          >
            Run Clustering:
          </Typography>
          <Box
            component="form"
            onSubmit={handleClustering}
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
              maxWidth: 400,
              mt: 1
            }}
          >
            <Box
              sx={{
                display: "flex",
                flexDirection: "row"
              }}
            >
              <TextField
                label="Max Distance (m)"
                type="number"
                value={maxDistance}
                onChange={(e) => setMaxDistance(e.target.value)}
                height="12px"
              />

              <TextField
                label="Max Yaw Difference (°)"
                type="number"
                value={maxYawDiff}
                onChange={(e) => setMaxYawDiff(e.target.value)}
                sx={{
                  ml: 1
                }}
              />
            </Box>
            <FormControlLabel
              control={
                <Checkbox
                  checked={resetExisting}
                  onChange={(e) => setResetExisting(e.target.checked)}
                />
              }
              label="Reset existing"
            />

            <Button
              type="submit"
              variant="contained"
            >
              Submit
            </Button>
          </Box>

          {loading && (
            <Box
              sx={{
                position: "absolute",
                inset: 0,
                bgcolor: "rgba(255,255,255,0.7)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                zIndex: 10,
              }}
            >
              <CircularProgress />
            </Box>
          )}

        </Box>
        <Box
          sx={{
            flex: 1,
            display: "flex",
            backgroundColor: "#F1F1F2",
            borderRadius: 2,
            ml: 1,
            p: 2,
            maxHeight: 310,
            overflow: 'auto',
            scrollbarWidth: "none",
            "&::-webkit-scrollbar": {
              display: "none"
            }
          }}
        >
          {responseData ?
            <Typography
              fontSize={14}
              sx={{
                color: "#003366"
              }}
              component="pre"
            >
              {JSON.stringify(responseData, null, 2)}
            </Typography>
            :
            <Typography
              fontSize={14}
              sx={{
                margin: "auto",
                color: "#B4B4B5",
              }}
            >
              please run an admin operation.
            </Typography>
          }
        </Box>
      </Box>
      <Box>
        <p>this is is where we will display all images</p>
      </Box>
    </Box >
  )
}

export default ImageAdminPage;
