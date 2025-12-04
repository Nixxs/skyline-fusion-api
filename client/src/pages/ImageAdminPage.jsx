import { useState, useEffect } from "react";
import axios from "axios";
import {
  Box,
  Typography,
  Button,
  TextField,
  FormControlLabel,
  Checkbox,
  CircularProgress,
  Tooltip,
} from "@mui/material";
import FileUploadOutlinedIcon from "@mui/icons-material/FileUploadOutlined";
import { DataGrid } from "@mui/x-data-grid";
import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";
import dayjs from "dayjs";

function ImageAdminPage() {
  const [loading, setLoading] = useState(false); // upload/cluster overlay
  const [file, setFile] = useState(null);
  const [maxDistance, setMaxDistance] = useState(2);
  const [maxYawDiff, setMaxYawDiff] = useState(5);
  const [resetExisting, setResetExisting] = useState(true);
  const [responseData, setResponseData] = useState(null);

  // Grid state
  const [images, setImages] = useState([]);
  const [rowCount, setRowCount] = useState(0);
  const [gridLoading, setGridLoading] = useState(false);

  // Grid filters
  const [searchName, setSearchName] = useState("");
  const [imageType, setImageType] = useState("");
  const [createdFrom, setCreatedFrom] = useState(null);
  const [createdTo, setCreatedTo] = useState(null);

  // Use the new paginationModel API (works reliably in v6/v7)
  const [paginationModel, setPaginationModel] = useState({
    page: 0, // 0-based for the grid
    pageSize: 50,
  });

  // Selection model (Set-based, as per our last working version)
  const [selectionModel, setSelectionModel] = useState({
    type: "include",
    ids: new Set(),
  });

  const apiBase = import.meta.env.VITE_API_URL;

  // -------------------------
  // Upload + clustering
  // -------------------------
  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0] || null;
    setFile(selectedFile);
    console.log("file set");
  };

  const handleUpload = async (event) => {
    event.preventDefault();
    if (!file) return;

    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(`${apiBase}/images`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      if (response.status === 201) {
        setResponseData(response.data);
        console.log("submitted file:", file.name);
        console.log(response.data);
        // Refresh grid after upload (reload current page)
        reloadGrid(paginationModel.page, paginationModel.pageSize);
      }
    } catch (error) {
      console.error(error);
      setResponseData(error);
    } finally {
      setLoading(false);
      setFile(null);
    }
  };

  const handleClustering = async (event) => {
    event.preventDefault();
    setLoading(true);

    const payload = {
      max_distance_m: Number(maxDistance),
      max_yaw_diff_deg: Number(maxYawDiff),
      reset_existing: resetExisting,
    };

    try {
      const response = await axios.post(`${apiBase}/images/cluster`, payload, {
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (response.status === 200) {
        setResponseData(response.data);
        console.log("sent payload", payload);
        // Refresh grid if clustering changes image state
        reloadGrid(paginationModel.page, paginationModel.pageSize);
      }
    } catch (error) {
      console.log(error);
      setResponseData(error);
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // Grid: columns
  // -------------------------
  const columns = [
    {
      field: "name",
      headerName: "Name",
      flex: 1,
      minWidth: 220,
    },
    {
      field: "image_type",
      headerName: "Type",
      width: 110,
    },
    {
      field: "created",
      headerName: "Captured",
      width: 190
    },
    {
      field: "imported_utc",
      headerName: "Imported (UTC)",
      width: 220
    },
    {
      field: "lon",
      headerName: "Lon",
      width: 120
    },
    {
      field: "lat",
      headerName: "Lat",
      width: 120
    },
    {
      field: "yaw_deg",
      headerName: "Yaw (°)",
      width: 110
    },
    {
      field: "target_range",
      headerName: "Target Range",
      width: 110
    },
    {
      field: "target_lon",
      headerName: "Target Lon",
      width: 110
    },
    {
      field: "target_lat",
      headerName: "Target Lat",
      width: 110
    }
  ];

  // -------------------------
  // Grid: data loading
  // -------------------------
  const reloadGrid = async (pageArg, pageSizeArg) => {
    setGridLoading(true);
    try {
      const response = await axios.get(`${apiBase}/images`, {
        params: {
          page: pageArg + 1, // API is 1-based
          page_size: pageSizeArg,
          ...(searchName ? { search: searchName } : {}), // only include the serach param if it is not null and exists
          ...(imageType ? { image_type: imageType } : {}),
          ...(createdFrom ? { created_from: createdFrom } : {}),
          ...(createdTo ? { created_to: createdTo } : {}),
        },
      });

      const data = response.data;
      console.log("images response", data);

      const rows = (data.items || []).map((img) => ({
        id: img.image_id, // DataGrid row id
        ...img,
      }));

      setImages(rows);
      setRowCount(data.total ?? 0);
    } catch (err) {
      console.error("Failed to load images", err);
    } finally {
      setGridLoading(false);
    }
  };

  const updateDataGrid = async () => {
    reloadGrid(paginationModel.page, paginationModel.pageSize);
  }

  const resetDataGrid = async () => {
    setSearchName(null);
    setImageType(null);
    setCreatedFrom(null);
    setCreatedTo(null);

    reloadGrid(paginationModel.page, paginationModel.pageSize)
  }

  // reload whenever page or pageSize changes
  useEffect(() => {
    reloadGrid(paginationModel.page, paginationModel.pageSize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paginationModel.page, paginationModel.pageSize]);

  // -------------------------
  // Grid: delete selected
  // -------------------------
  const handleDeleteSelected = async () => {
    const idsSet = selectionModel.ids;
    const hasSelection = idsSet && idsSet.size > 0;
    if (!hasSelection) return;

    const idsToDelete = Array.from(idsSet);
    console.log("Deleting image_ids:", idsToDelete);

    if (
      !window.confirm(
        `Delete ${idsToDelete.length} selected image(s)? This cannot be undone.`
      )
    ) {
      return;
    }

    try {
      setGridLoading(true);
      const res = await axios.delete(`${apiBase}/images/batch`, {
        data: {
          image_ids: idsToDelete,
        },
      });

      console.log("Delete response:", res.data);

      // Optimistic local update
      setImages((prev) => prev.filter((row) => !idsSet.has(row.id)));
      setRowCount((prev) => Math.max(prev - idsToDelete.length, 0));

      // Clear selection
      setSelectionModel({
        type: "include",
        ids: new Set(),
      });
    } catch (err) {
      console.error("Failed to delete images", err);
      alert("Failed to delete images – check console for details.");
    } finally {
      setGridLoading(false);
    }
  };

  const selectedCount = selectionModel.ids ? selectionModel.ids.size : 0;

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        padding: 1,
        minWidth: 1400,
        maxWidth: 1800,
        height: "100vh",            // full viewport height
        boxSizing: "border-box",
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
              sx={{
                display: "none"
              }}
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

      {/* Bottom: DataGrid */}
      <Box
        sx={{
          mt: 2,
          display: "flex",
          flexDirection: "column",
          flexGrow: 1,            // <- take all remaining vertical space
          minHeight: 0,
        }}
      >
        <Box
          sx={{
            mb: 1,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Box
            sx={{
              display: "flex",
              gap: "5px",
              alignItems: 'left',
            }}
          >
            <TextField
              label="Search Name"
              type="text"
              value={searchName}
              onChange={(e) => setSearchName(e.target.value)}
              height="12px"
            />

            <TextField
              label="Image Type"
              type="text"
              value={imageType}
              onChange={(e) => setImageType(e.target.value)}
              height="12px"
            />

            <DateTimePicker
              label="Captured From"
              value={createdFrom ? dayjs(createdFrom) : null}
              onChange={(newValue) => {
                const formatted = newValue
                  ? newValue.format("YYYY-MM-DDTHH:mm:ss")
                  : null;
                setCreatedFrom(formatted);
              }}
              slotProps={{
                textField: {
                  size: "small"
                }
              }}
            />

            <DateTimePicker
              label="Captured To"
              value={createdFrom ? dayjs(createdTo) : null}
              onChange={(newValue) => {
                const formatted = newValue
                  ? newValue.format("YYYY-MM-DDTHH:mm:ss")
                  : null;
                setCreatedTo(formatted);
              }}
              slotProps={{
                textField: {
                  size: "small"
                }
              }}
            />

            <Button
              variant="outlined"
              size="small"
              onClick={resetDataGrid}
            >
              Reset
            </Button>

            <Button
              variant="contained"
              size="small"
              onClick={updateDataGrid}
            >
              Apply Search
            </Button>
          </Box>

          <Button
            variant="outlined"
            color="error"
            size="small"
            disabled={selectedCount === 0 || gridLoading}
            onClick={handleDeleteSelected}
          >
            Delete selected ({selectedCount})
          </Button>
        </Box>
        <Box
          sx={{
            display: "flex",
            flex: 1,         // ⬅ fill remaining vertical space
            minHeight: 0,    // ⬅ allow inner boxes to shrink and have internal scroll
            overflow: "hidden",
          }}
        >
          <Box
            sx={{
              flex: 2,        // ⬅ give grid more space than right panel
              minWidth: 0,    // ⬅ allow proper flex overflow handling
              minHeight: 0,
              mr: 1,
            }}
          >
            <DataGrid
              rows={images}
              columns={columns}
              checkboxSelection
              disableRowSelectionOnClick
              disableRowSelectionExcludeModel
              paginationMode="server"
              rowCount={rowCount}
              loading={gridLoading}
              // NEW pagination wiring
              paginationModel={paginationModel}
              onPaginationModelChange={(newModel) => {
                // reset selection when changing page/size
                setSelectionModel({
                  type: "include",
                  ids: new Set(),
                });
                setPaginationModel(newModel);
              }}
              // selection wiring (as before)
              rowSelectionModel={selectionModel}
              onRowSelectionModelChange={(newSelectionModel) => {
                console.log("New selection model:", newSelectionModel);
                setSelectionModel(newSelectionModel);
              }}
              density="compact"
              sx={{
                height: "100%",
                backgroundColor: "#F1F1F2",
                color: "#000",
                borderRadius: 2,

                /* HEADER */
                "& .MuiDataGrid-columnHeaders": {
                  backgroundColor: "#E0E0E0 !important",
                  color: "#000 !important",
                  borderBottom: "1px solid #BDBDBD",
                },
                "& .MuiDataGrid-columnHeader": {
                  backgroundColor: "#E0E0E0 !important",
                  color: "#000 !important",
                },
                "& .MuiDataGrid-columnHeaderTitle": {
                  color: "#000 !important",
                  fontWeight: 600,
                },

                /* FOOTER */
                "& .MuiDataGrid-footerContainer": {
                  backgroundColor: "#E0E0E0 !important",
                  color: "#000 !important",
                  borderTop: "1px solid #BDBDBD",
                },

                /* ROW STRIPING */
                "& .MuiDataGrid-row:nth-of-type(odd)": {
                  backgroundColor: "#FFFFFF",
                },
                "& .MuiDataGrid-row:nth-of-type(even)": {
                  backgroundColor: "#F9F9F9",
                },

                "& .MuiDataGrid-cell": {
                  borderColor: "#DDD",
                  color: "#000",
                },

                /* HOVER + SELECTION */
                "& .MuiDataGrid-row:hover": {
                  backgroundColor: "#EEF3FF !important",
                },
                "& .MuiDataGrid-row.Mui-selected": {
                  backgroundColor: "#D6E4FF !important",
                },
                "& .MuiDataGrid-row.Mui-selected:hover": {
                  backgroundColor: "#C7D8FF !important",
                },
              }}
            />
          </Box>
          <Box
            sx={{
              flexBasis: 320,       // ⬅ fixed-ish width for side panel
              flexShrink: 0,
              height: "100%",
              backgroundColor: "#fafafa",
              borderRadius: 2,
              p: 2,
              overflow: "auto",
            }}
          >
            <Typography variant="body2">selected image thumbnails</Typography>
          </Box>
        </Box>
      </Box>
    </Box >
  );
}

export default ImageAdminPage;
