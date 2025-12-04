import { Box } from "@mui/material";
import { ReactPhotoSphereViewer } from "react-photo-sphere-viewer";
import { useRef } from "react";

export default function PanoViewer({ src, onViewChange }) {
  const viewerRef = useRef(null);

  const handleReady = (viewer) => {
    // viewer is the Photo Sphere Viewer instance
    viewerRef.current = viewer;

    const emitViewState = () => {
      const { yaw, pitch } = viewer.getPosition();
      const fov = viewer.getFov ? viewer.getFov() : undefined;
      onViewChange?.({ yaw, pitch, fov });
    };

    // fire once on ready
    emitViewState();

    // subscribe to position + zoom changes
    viewer.addEventListener("position-updated", emitViewState);
    viewer.addEventListener("zoom-updated", emitViewState);
  };

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
        minFov={1}      // allow very deep zoom
        maxFov={120}    // wide angle zoom out
        defaultZoomLvl={50}
        onReady={handleReady}
        rendererParameters={{
          alpha: true,
          antialias: true,
          preserveDrawingBuffer: true,
        }}
      />
    </Box>
  );
}
