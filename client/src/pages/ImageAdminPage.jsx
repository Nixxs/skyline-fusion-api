import { useState } from 'react';
import axios from "axios";
import {
  Box,
  Typography,
  Button,
  TextField,
  FormControlLabel,
  Checkbox
} from "@mui/material";
import FileUploadOutlinedIcon from '@mui/icons-material/FileUploadOutlined';

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

  const handleUpload = (event) => {
    event.preventDefault();
    setLoading(true);


    console.log('Submitting file:', file.name);

    setFile(null);
    setLoading(false);
  }

  const handleClustering = (event) => {
    event.preventDefault();
    setLoading(true);

    const payload = {
      max_distance_m: Number(maxDistance),
      max_yaw_diff_deg: Number(maxYawDiff),
      reset_existing: resetExisting,
    };

    // send the request to cluster images
    // get data back and display in the right box

    console.log("sent payload", payload);

    setLoading(false);
  }

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        padding: 1
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
            flexDirection: "column"
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
                onChange={handleFileChange}
              />
            </Button>
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
        </Box>
        <Box
          sx={{
            flex: 1,
            display: "flex",
            backgroundColor: "#F1F1F2",
            borderRadius: 2,
            ml: 1,
            p: 2
          }}
        >
          {responseData ? responseData :
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
    </Box>
  )
}

export default ImageAdminPage;
