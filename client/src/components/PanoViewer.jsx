import { Box } from "@mui/material";
import { ReactPhotoSphereViewer } from "react-photo-sphere-viewer";

export default function PanoViewer({ src }) {
  return (
    <Box
      sx={{
        width: "100%",
        height: "100%",
        borderRadius: 1,
        overflow: "hidden",
        border: "1px solid rgba(255,255,255,0.1)",
      }}
    >
      <ReactPhotoSphereViewer
        src={src}
        height="100%"
        width="100%"
        navbar={true}
        minFov={1}     // allow very deep zoom (default ~30-50)
        maxFov={120}    // wide angle zoom out more if desired
        defaultZoomLvl={50} // 0 = allow full zoom range
      />
    </Box>
  );
}

