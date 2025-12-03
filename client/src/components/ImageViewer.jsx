import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import AddIcon from "@mui/icons-material/Add";
import RemoveIcon from "@mui/icons-material/Remove";
import RestartAltIcon from "@mui/icons-material/RestartAlt";
import { Stack, Box, IconButton } from "@mui/material";


export default function ImageViewer({ selectedImage }) {
  return (
    <TransformWrapper
      initialScale={1}
      minScale={0.5}
      maxScale={10}
      wheel={{ step: 0.1 }} // how much zoom per wheel "tick"
    >
      {({ zoomIn, zoomOut, resetTransform }) => (
        <>
          {/* Controls */}
          <Stack
            direction="row"
            spacing={1}
            sx={{ position: "absolute", bottom: 8, left: 8, zIndex: 10 }}
          >
            <IconButton
              size="small"
              color="white"
              onClick={() => zoomIn()}
            >
              <AddIcon />
            </IconButton>
            <IconButton
              size="small"
              color="white"
              onClick={() => zoomOut()}
            >
              <RemoveIcon />
            </IconButton>
            <IconButton
              size="small"
              color="white"
              onClick={() => resetTransform()}
            >
              <RestartAltIcon />
            </IconButton>
          </Stack>

          {/* Zoomable / pannable area */}
          <TransformComponent
            wrapperStyle={{
              width: "100%",
              height: "100%",
              overflow: "hidden",
              cursor: "grab",
            }}
          >
            <Box
              component="img"
              src={selectedImage.signed_url}
              alt={selectedImage.name}
              sx={{
                maxWidth: "100%",
                maxHeight: "100%",
                objectFit: "contain",
                display: "block",
              }}
              // Optional: keep the click-to-open behavior
              onClick={() =>
                window.open(
                  selectedImage.signed_url,
                  "_blank",
                  "noopener,noreferrer"
                )
              }
            />
          </TransformComponent>
        </>
      )}
    </TransformWrapper>
  )
}
