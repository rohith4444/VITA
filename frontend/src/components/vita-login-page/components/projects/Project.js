import React from "react";
import './project.css';
import TextInput from "../../../common/textinput/TextInput";
import CustomButton from "../../../common/button/CustomButton";
import InputAdornment from '@mui/material/InputAdornment';
import IconButton from '@mui/material/IconButton';
import { SearchOutlined, Tune } from '@mui/icons-material';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';

const projects = [
    { title: "AETHER AI", description: "description", updated: "1 day ago" },
    { title: "VITA", description: "description", updated: "1 month ago" },
    { title: "Integrate DDS and dev py Package", description: "description", updated: "6 months ago" },
    { title: "Comp-HuSim", description: "description", updated: "6 months ago" },
    { title: "LinDer", description: "description", updated: "6 months ago" },
    { title: "How to use Claude", description: "description", updated: "6 months ago" }
];

const Project = ({ setStateProject, ...props }) => {

    const [open, setOpen] = React.useState(false);

    const handleClickOpen = () => {
        setOpen(true);
    };

    const handleClose = () => {
        setOpen(false);
    };

    return (<>
        <div className="project-wrapper">
            <div className="top-search">
                <div className="left-new-project">
                    <h2>All your Projects</h2>
                </div>
                <div className="right-search-project">
                    <CustomButton version="v2" onClick={handleClickOpen}>New Project</CustomButton>
                </div>
            </div>
            <div className="top-search">
                <div className="left-new-project">
                    <TextInput size="small"
                        label="Enter text to search"
                        InputProps={{
                            endAdornment: (
                                <InputAdornment>
                                    <IconButton>
                                        <SearchOutlined />
                                    </IconButton>
                                </InputAdornment>
                            )
                        }}
                    />
                </div>
                <div className="right-search-project">
                    <CustomButton><Tune />&nbsp;&nbsp;Filters</CustomButton>
                </div>
            </div>
            <div className="recent-projects">
                {/* {Array.from({ length: 10 }).map((_, index) => (
                    <div className="project-card" key={index} onClick={setStateProject}>
                        <h3 className="project-title">Title-{index}</h3>
                        <p className="project-description">Description-{index}</p>
                        <p className="project-updated">Updated</p>
                    </div>
                ))} */}
                {projects.map((project, index) => (
                    <div className="project-card" key={index} onClick={setStateProject}>
                        <h3 className="project-title">{project.title}</h3>
                        <p className="project-description">{project.description}</p>
                        <p className="project-updated">Updated {project.updated}</p>
                    </div>
                ))}
            </div>
        </div>
        <Dialog
            open={open}
            onClose={handleClose}
            disableEnforceFocus={true}
            sx={{
                // 👇 Another option to style Paper
                "& .MuiDialog-paper": {
                  borderRadius: "1rem",
                  padding: "1rem"
                },
              }}
            slotProps={{
                paper: {
                    component: 'form',
                    onSubmit: (event) => {
                        event.preventDefault();
                        const formData = new FormData(event.currentTarget);
                        const formJson = Object.fromEntries(formData.entries());
                        const name = formJson.name;
                        const description = formJson.description;
                        console.log(name, description);
                        handleClose();
                    },
                },
            }}
        >
            <DialogTitle>Add new project</DialogTitle>
            <DialogContent>
                <DialogContentText>
                    
                </DialogContentText>
                <TextInput
                    autoFocus
                    required
                    margin="dense"
                    id="name"
                    name="name"
                    label="Enter name of the project"
                    fullWidth
                    size="small"
                />
                <TextInput
                    required
                    margin="dense"
                    id="description"
                    name="description"
                    label="Enter description of the project"
                    fullWidth
                    multiline
                    size="small"
                    rows={4}
                />
            </DialogContent>
            <DialogActions>
                <CustomButton onClick={handleClose}>Cancel</CustomButton>
                <CustomButton type="submit">Save</CustomButton>
            </DialogActions>
        </Dialog>
    </>
    );
}

export default Project